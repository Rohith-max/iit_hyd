"""LangGraph orchestrator — builds and runs the credit analysis pipeline."""
import asyncio
import logging
import uuid
from typing import Dict

from app.agents.state import CreditAnalysisState
from app.agents.data_ingestor import DataIngestorAgent
from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.web_research import WebResearchAgent
from app.agents.risk_assessor import RiskAssessmentAgent
from app.agents.cam_writer import CAMWriterAgent
from app.agents.ws_manager import ws_manager

logger = logging.getLogger(__name__)


class CreditAnalysisPipeline:
    """Sequential agent pipeline for credit analysis."""

    def __init__(self):
        self.data_ingestor = DataIngestorAgent()
        self.financial_analyst = FinancialAnalystAgent()
        self.web_researcher = WebResearchAgent()
        self.risk_assessor = RiskAssessmentAgent()
        self.cam_writer = CAMWriterAgent()

    async def run_analysis(self, case_id: str, case_data: dict) -> CreditAnalysisState:
        """Run full credit analysis pipeline."""
        state: CreditAnalysisState = {
            "case_id": case_id,
            "company_name": case_data.get("company_name", ""),
            "cin": case_data.get("cin", ""),
            "industry_code": case_data.get("industry_code", ""),
            "requested_amount": float(case_data.get("requested_amount", 0) or 0),
            "loan_type": case_data.get("loan_type", "TERM_LOAN"),
            "raw_financials": {},
            "processed_financials": {},
            "financial_spreads": [],
            "web_research": {},
            "news_sentiment": {},
            "regulatory_flags": [],
            "company_meta": {},
            "bureau_data": {},
            "collateral_data": case_data.get("collateral_data", {}),
            "macro_data": {},
            "ml_features": {},
            "ml_scores": {},
            "early_warnings": [],
            "cam_sections": {},
            "current_agent": "DataIngestor",
            "agent_logs": [],
            "errors": [],
            "status": "PROCESSING",
        }

        await ws_manager.broadcast(case_id, {
            "type": "pipeline_start",
            "total_agents": 5,
            "agents": ["DataIngestor", "FinancialAnalyst", "WebResearch", "RiskAssessment", "CAMWriter"],
        })

        agents = [
            ("DataIngestor", self.data_ingestor),
            ("FinancialAnalyst", self.financial_analyst),
            ("WebResearch", self.web_researcher),
            ("RiskAssessment", self.risk_assessor),
            ("CAMWriter", self.cam_writer),
        ]

        for agent_name, agent in agents:
            try:
                await ws_manager.broadcast(case_id, {
                    "type": "agent_start",
                    "agent": agent_name,
                })
                state = await agent.run(state)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
                state["errors"].append(f"{agent_name}: {str(e)}")
                state["status"] = "ERROR"
                await ws_manager.broadcast(case_id, {
                    "type": "agent_error",
                    "agent": agent_name,
                    "error": str(e),
                })

        await ws_manager.broadcast(case_id, {
            "type": "pipeline_complete",
            "status": state["status"],
            "decision": state.get("ml_scores", {}).get("decision", "UNKNOWN"),
        })

        return state


pipeline = CreditAnalysisPipeline()
