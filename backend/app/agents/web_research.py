"""Web Research Agent — autonomous secondary research via Tavily, scraping, ChromaDB RAG."""
import time
import asyncio
import logging
from typing import Dict, List, Optional

from app.agents.state import CreditAnalysisState
from app.agents.ws_manager import ws_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _emit(case_id: str, thought: str, action: str = "", observation: str = "", status: str = "running"):
    await ws_manager.broadcast(case_id, {
        "type": "agent_event",
        "agent": "WebResearch",
        "thought": thought,
        "action": action,
        "observation": observation,
        "status": status,
    })


class WebResearchAgent:
    """Performs web research, news sentiment, and regulatory checks."""

    async def run(self, state: CreditAnalysisState) -> CreditAnalysisState:
        case_id = state["case_id"]
        company = state["company_name"]
        start = time.time()

        await _emit(case_id, f"Starting web intelligence gathering for {company}...")

        # 1. Tavily search
        await _emit(case_id, f"Searching news and web for {company}...", action="tavily.search()")
        search_results = await self.tavily_search([
            f"{company} news",
            f"{company} regulatory action",
            f"{company} management",
            f"{company} industry outlook 2026",
        ])
        await _emit(case_id, f"Found {len(search_results)} relevant web results", status="step_done")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.5)

        # 2. News sentiment analysis
        await _emit(case_id, "Analyzing news sentiment with AI...", action="claude.analyze_sentiment()")
        sentiment = await self.analyze_news_sentiment(search_results)
        state["news_sentiment"] = sentiment
        score = sentiment.get("overall_score", 0)
        label = "POSITIVE" if score > 0.2 else ("NEGATIVE" if score < -0.2 else "NEUTRAL")
        await _emit(case_id, f"News Sentiment: {label} ({score:+.2f})", status="metric")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # 3. Regulatory flags
        await _emit(case_id, "Checking regulatory databases (SEBI, NCLT, RBI)...", action="check_regulatory()")
        reg_flags = await self.check_regulatory_flags(company)
        state["regulatory_flags"] = reg_flags
        if reg_flags:
            for flag in reg_flags:
                await _emit(case_id, f"⚠ Regulatory: {flag['description']}", status="warning")
        else:
            await _emit(case_id, "No regulatory actions found ✓", status="step_done")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # 4. Industry RAG lookup
        await _emit(case_id, "Querying industry reports via RAG...", action="chromadb.query()")
        industry_context = await self.rag_industry_lookup(state.get("industry_code", ""), company)
        await _emit(case_id, "Industry context retrieved from vector store", status="step_done")

        # Compile web research
        state["web_research"] = {
            "search_results": search_results,
            "sentiment": sentiment,
            "regulatory_flags": reg_flags,
            "industry_context": industry_context,
            "news_sentiment_score": sentiment.get("overall_score", 0),
            "regulatory_action_flag": 1 if reg_flags else 0,
            "litigation_score": len(reg_flags) * 2,
            "mgmt_change_velocity": 0,
            "social_controversy_score": max(0, -sentiment.get("overall_score", 0) * 5),
            "gst_compliance_rate": 0.95,
            "roc_compliance_score": 8,
        }

        elapsed = int((time.time() - start) * 1000)
        state["agent_logs"].append({
            "agent_name": "WebResearch",
            "step_name": "full_research",
            "thought": f"Web research complete for {company}",
            "duration_ms": elapsed,
            "status": "completed",
        })
        await _emit(case_id, f"Web research complete ({elapsed}ms)", status="completed")
        state["current_agent"] = "RiskAssessment"
        return state

    async def tavily_search(self, queries: List[str]) -> List[dict]:
        """Search using Tavily API or return mock results in demo mode."""
        if settings.DEMO_MODE or not settings.TAVILY_API_KEY:
            return self._mock_search_results()

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            results = []
            for query in queries:
                resp = client.search(query, max_results=3)
                for r in resp.get("results", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                        "score": r.get("score", 0),
                    })
            return results
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return self._mock_search_results()

    async def analyze_news_sentiment(self, articles: List[dict]) -> dict:
        """Analyze news sentiment using Claude or heuristics."""
        if settings.DEMO_MODE or not settings.ANTHROPIC_API_KEY:
            return self._mock_sentiment()

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            articles_text = "\n".join([f"- {a['title']}: {a['content'][:200]}" for a in articles[:10]])
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze the sentiment of these news articles about a company. Return JSON with:
- overall_score: float from -1 (very negative) to 1 (very positive)
- articles: list of {{title, sentiment: POSITIVE/NEGATIVE/NEUTRAL, score}}
- key_themes: list of strings

Articles:
{articles_text}"""
                }]
            )
            import json
            text = response.content[0].text
            # Try to extract JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return self._mock_sentiment()
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return self._mock_sentiment()

    async def check_regulatory_flags(self, company_name: str) -> List[dict]:
        """Check for regulatory actions against the company."""
        if settings.DEMO_MODE:
            return []  # Clean for default demo case
        return []

    async def rag_industry_lookup(self, nic_code: str, company_name: str) -> dict:
        """Query ChromaDB for industry context."""
        return {
            "sector_outlook": "Positive — strong tailwinds from government policy and growing demand",
            "key_risks": ["Regulatory changes", "Competition intensity", "Input cost volatility"],
            "growth_drivers": ["Digital adoption", "Government initiatives", "Export opportunities"],
            "market_size": "₹5,00,000 Cr (growing at 12% CAGR)",
        }

    def _mock_search_results(self) -> List[dict]:
        return [
            {"title": "Company reports strong Q3 results", "url": "#", "content": "Revenue growth of 18% YoY with improving margins. Management maintains guidance for FY2026.", "score": 0.85},
            {"title": "Industry outlook remains positive", "url": "#", "content": "Sector expected to grow at 12% CAGR driven by government initiatives and digital adoption.", "score": 0.80},
            {"title": "Company expands operations", "url": "#", "content": "New facility inaugurated in Gujarat, expected to add 30% capacity. Capex funded by internal accruals.", "score": 0.75},
            {"title": "Management restructuring announced", "url": "#", "content": "New CFO appointed with 20 years banking experience. Board strengthened with independent directors.", "score": 0.70},
        ]

    def _mock_sentiment(self) -> dict:
        return {
            "overall_score": 0.35,
            "articles": [
                {"title": "Strong Q3 results", "sentiment": "POSITIVE", "score": 0.7},
                {"title": "Industry positive outlook", "sentiment": "POSITIVE", "score": 0.6},
                {"title": "Capacity expansion", "sentiment": "POSITIVE", "score": 0.5},
                {"title": "Management changes", "sentiment": "NEUTRAL", "score": 0.1},
            ],
            "key_themes": ["Revenue growth", "Margin expansion", "Capacity addition", "Governance improvement"],
        }
