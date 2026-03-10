"""Case management API routes — in-memory store (no PostgreSQL required)."""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from app.api.schemas import (
    CaseCreateRequest, CaseResponse, CaseListResponse,
    DecisionResponse, MLScoreResponse, EWSResponse, CAMResponse,
)
from app.agents.orchestrator import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

# --------------- In-memory stores ---------------
_cases: Dict[str, dict] = {}          # case_id -> case dict
_ml_scores: Dict[str, dict] = {}      # case_id -> score dict
_cam_docs: Dict[str, dict] = {}       # case_id -> cam dict
_ews_signals: Dict[str, list] = {}    # case_id -> [signal, ...]
_spreads: Dict[str, list] = {}        # case_id -> [spread, ...]


def _next_case_number() -> str:
    return f"CAM-2026-{uuid.uuid4().hex[:4].upper()}"


def _case_response(c: dict) -> CaseResponse:
    return CaseResponse(
        id=c["id"], case_number=c["case_number"], company_name=c["company_name"],
        cin=c.get("cin"), gstin=c.get("gstin"), pan=c.get("pan"),
        industry_code=c.get("industry_code"), loan_type=c.get("loan_type"),
        requested_amount=c.get("requested_amount"),
        requested_tenure_months=c.get("requested_tenure_months"),
        purpose=c.get("purpose"), status=c["status"],
        created_at=c.get("created_at"), updated_at=c.get("updated_at"),
        priority=c.get("priority", "NORMAL"),
    )


@router.post("", response_model=CaseResponse)
async def create_case(req: CaseCreateRequest):
    case_id = str(uuid.uuid4())
    now = datetime.utcnow()
    case = {
        "id": case_id,
        "case_number": _next_case_number(),
        "company_name": req.company_name,
        "cin": req.cin, "gstin": req.gstin, "pan": req.pan,
        "industry_code": req.industry_code,
        "loan_type": req.loan_type,
        "requested_amount": req.requested_amount,
        "requested_tenure_months": req.requested_tenure_months,
        "purpose": req.purpose,
        "collateral_data": {
            "collateral_type": req.collateral_type or "immovable_property",
            "collateral_value": req.collateral_value or 0,
            "collateral_description": req.collateral_description or "",
        } if req.collateral_type or req.collateral_value else {},
        "status": "INTAKE",
        "priority": "NORMAL",
        "created_at": now,
        "updated_at": now,
    }
    _cases[case_id] = case
    return _case_response(case)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
):
    all_cases = sorted(_cases.values(), key=lambda c: c["created_at"], reverse=True)
    if status:
        all_cases = [c for c in all_cases if c["status"] == status]
    total = len(all_cases)
    offset = (page - 1) * page_size
    page_cases = all_cases[offset:offset + page_size]
    return CaseListResponse(
        cases=[_case_response(c) for c in page_cases],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return _case_response(case)


@router.post("/{case_id}/analyze")
async def trigger_analysis(case_id: str, background_tasks: BackgroundTasks):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    case["status"] = "PROCESSING"
    case["updated_at"] = datetime.utcnow()

    case_data = {
        "company_name": case["company_name"],
        "cin": case.get("cin"),
        "industry_code": case.get("industry_code"),
        "requested_amount": case.get("requested_amount", 0),
        "loan_type": case.get("loan_type"),
        "requested_tenure_months": case.get("requested_tenure_months"),
        "collateral_data": case.get("collateral_data", {}),
    }

    background_tasks.add_task(_run_pipeline, case_id, case_data)
    return {"status": "PROCESSING", "case_id": case_id, "message": "Analysis pipeline started"}


async def _run_pipeline(case_id: str, case_data: dict):
    """Background task to run the full analysis pipeline and persist results in memory."""
    try:
        state = await pipeline.run_analysis(case_id, case_data)

        case = _cases.get(case_id)
        if case:
            decision = state.get("ml_scores", {}).get("decision", "ERROR")
            case["status"] = "ERROR" if state.get("status") == "ERROR" else decision
            case["updated_at"] = datetime.utcnow()

        # Save financial spreads
        _spreads[case_id] = state.get("financial_spreads", [])

        # Save ML scores
        scores = state.get("ml_scores", {})
        if scores:
            _ml_scores[case_id] = {**scores, "scored_at": datetime.utcnow()}

        # Save CAM
        cam_sections = state.get("cam_sections", {})
        if cam_sections:
            total_words = sum(len(s.get("content", "").split()) for s in cam_sections.values() if isinstance(s, dict))
            _cam_docs[case_id] = {
                "version": 1,
                "sections": cam_sections,
                "word_count": total_words,
                "generated_at": datetime.utcnow(),
            }

        # Save EWS
        _ews_signals[case_id] = state.get("early_warnings", [])

    except Exception as e:
        logger.error(f"Pipeline failed for case {case_id}: {e}", exc_info=True)
        case = _cases.get(case_id)
        if case:
            case["status"] = "ERROR"
            case["updated_at"] = datetime.utcnow()


@router.get("/{case_id}/status")
async def get_case_status(case_id: str):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return {"case_id": case_id, "status": case["status"]}


@router.get("/{case_id}/decision", response_model=DecisionResponse)
async def get_decision(case_id: str):
    case = _cases.get(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    scores = _ml_scores.get(case_id)
    if not scores:
        raise HTTPException(404, "Decision not yet available")

    ews_list = _ews_signals.get(case_id, [])

    return DecisionResponse(
        case_id=case_id,
        company_name=case["company_name"],
        decision=scores.get("decision", "ERROR"),
        ml_score=MLScoreResponse(
            pd_score=scores.get("pd_score", 0),
            lgd_score=scores.get("lgd_score", 0),
            ead=scores.get("ead", 0),
            expected_loss=scores.get("expected_loss", 0),
            credit_grade=scores.get("credit_grade", "NR"),
            credit_score=scores.get("credit_score", 0),
            recommended_limit=scores.get("recommended_limit", 0),
            recommended_rate=scores.get("recommended_rate", 0),
            risk_premium=scores.get("risk_premium", 0),
            decision=scores.get("decision", "ERROR"),
            confidence=scores.get("confidence", 0),
            shap_values=scores.get("shap_values"),
            feature_importances=scores.get("feature_importances"),
            scored_at=scores.get("scored_at"),
        ),
        early_warnings=ews_list,
    )


@router.get("/{case_id}/cam")
async def get_cam(case_id: str):
    cam = _cam_docs.get(case_id)
    if not cam:
        raise HTTPException(404, "CAM not yet generated")
    return CAMResponse(
        case_id=case_id,
        version=cam["version"],
        sections=cam["sections"],
        word_count=cam["word_count"],
        generated_at=cam.get("generated_at"),
    )


@router.get("/{case_id}/cam/pdf")
async def get_cam_pdf(case_id: str):
    from fastapi.responses import Response
    from app.services.pdf_service import generate_cam_pdf

    cam = _cam_docs.get(case_id)
    if not cam:
        raise HTTPException(404, "CAM not yet generated")

    case = _cases.get(case_id, {})
    scores = _ml_scores.get(case_id, {})
    pdf_bytes = generate_cam_pdf(
        cam["sections"],
        {"case_number": case.get("case_number", "N/A"), "company_name": case.get("company_name", "N/A")},
        ml_scores=scores,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CAM_{case.get('case_number', case_id)}.pdf"},
    )


@router.get("/{case_id}/ews")
async def get_ews(case_id: str):
    signals = _ews_signals.get(case_id, [])
    return [
        EWSResponse(
            signal_type=s.get("signal_type", ""),
            severity=s.get("severity", ""),
            description=s.get("description", ""),
            triggered_by=s.get("triggered_by", ""),
            detected_at=s.get("detected_at"),
        )
        for s in signals
    ]


@router.get("/{case_id}/shap")
async def get_shap(case_id: str):
    scores = _ml_scores.get(case_id)
    if not scores:
        raise HTTPException(404, "SHAP data not available")
    return {
        "waterfall_data": scores.get("shap_values", []),
        "natural_language_summary": scores.get("shap_summary", ""),
        "risk_radar": scores.get("feature_importances", {}),
        "ai_analysis": scores.get("ai_analysis"),
    }
