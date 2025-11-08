"""LangGraph-based extraction service using Vertex AI."""
import json
import time
from typing import Dict, Any, TypedDict
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from pydantic import ValidationError

from models.schemas import ProcessedEvent, ExtractedData
from config import settings


class ExtractionState(TypedDict):
    """State for LangGraph extraction workflow."""
    processed_event: ProcessedEvent
    extracted_data: Dict[str, Any]
    confidence: float
    errors: list


class ExtractionService:
    """LangGraph-based extraction service for structured data extraction."""
    
    def __init__(self):
        self.llm = ChatVertexAI(
            model_name=settings.vertex_ai_model,
            temperature=0.1,
            location=settings.vertex_ai_location,
            project=settings.gcp_project_id,
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for extraction."""
        workflow = StateGraph(ExtractionState)
        
        # Add nodes
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("enrich", self._enrich_node)
        
        # Define edges
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_enrich,
            {
                "enrich": "enrich",
                "end": END,
            }
        )
        workflow.add_edge("enrich", END)
        
        return workflow.compile()
    
    async def extract(self, processed_event: ProcessedEvent) -> ExtractedData:
        """
        Extract structured data from processed event.
        
        Args:
            processed_event: Processed interaction event
            
        Returns:
            ExtractedData: Structured extracted data
        """
        start_time = time.time()
        
        # Initialize state
        initial_state: ExtractionState = {
            "processed_event": processed_event,
            "extracted_data": {},
            "confidence": 0.0,
            "errors": [],
        }
        
        # Run graph
        result = await self.graph.ainvoke(initial_state)
        
        # Parse and validate extracted data
        try:
            extracted_data = ExtractedData(**result["extracted_data"])
        except ValidationError as e:
            # Fallback: create minimal valid response
            extracted_data = ExtractedData(
                summary=processed_event.raw_text[:500] if processed_event.raw_text else "No content available",
                contacts=[],
            )
            result["errors"].append(str(e))
            result["confidence"] = 0.3
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return extracted_data, result["confidence"], processing_time_ms
    
    async def _extract_node(self, state: ExtractionState) -> ExtractionState:
        """Extract structured data using LLM with JSON schema constraint."""
        processed_event = state["processed_event"]
        
        # Build extraction prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CRM data extraction assistant. Extract structured information from the following interaction text.

Extract the following information:
- contacts: List of people mentioned (full_name, title, email, company)
- company: Company name mentioned
- deal_value: Numeric value of any deal mentioned
- currency: Currency code (default: USD)
- next_step: Next action item or step mentioned
- follow_up_date: Date in YYYY-MM-DD format if mentioned
- sentiment: positive, neutral, or negative
- risk_flags: List of any risk indicators or concerns
- summary: Concise summary of the interaction (REQUIRED)
- action_items: List of specific action items mentioned

Return ONLY valid JSON matching this schema:
{{
  "contacts": [{{"full_name": "...", "title": "...", "email": "...", "company": "..."}}],
  "company": "...",
  "deal_value": 0.0,
  "currency": "USD",
  "next_step": "...",
  "follow_up_date": "YYYY-MM-DD",
  "sentiment": "positive|neutral|negative",
  "risk_flags": ["..."],
  "summary": "...",
  "action_items": ["..."]
}}"""),
            ("human", "Extract information from this interaction:\n\n{text}")
        ])
        
        # Get text to extract from
        text = processed_event.transcript or processed_event.raw_text or ""
        
        # Create chain
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            extracted = await chain.ainvoke({"text": text})
            state["extracted_data"] = extracted
            state["confidence"] = 0.8  # Initial confidence
        except Exception as e:
            state["errors"].append(f"Extraction error: {str(e)}")
            # Fallback extraction
            state["extracted_data"] = {
                "summary": text[:500] if text else "No content available",
                "contacts": [],
                "action_items": [],
                "risk_flags": [],
            }
            state["confidence"] = 0.3
        
        return state
    
    async def _validate_node(self, state: ExtractionState) -> ExtractionState:
        """Validate extracted data against schema."""
        try:
            # Validate against Pydantic model
            extracted = ExtractedData(**state["extracted_data"])
            state["extracted_data"] = extracted.model_dump()
            
            # Increase confidence if validation passes
            if state["confidence"] < 0.9:
                state["confidence"] = min(state["confidence"] + 0.1, 0.9)
        except ValidationError as e:
            state["errors"].append(f"Validation error: {str(e)}")
            # Ensure summary exists (required field)
            if "summary" not in state["extracted_data"] or not state["extracted_data"]["summary"]:
                text = state["processed_event"].raw_text or ""
                state["extracted_data"]["summary"] = text[:500] if text else "No content available"
            state["confidence"] = max(state["confidence"] - 0.2, 0.3)
        
        return state
    
    async def _enrich_node(self, state: ExtractionState) -> ExtractionState:
        """Enrich extracted data with additional context."""
        # This node can be used for additional enrichment
        # For now, we'll just increase confidence slightly
        if state["confidence"] < 0.95:
            state["confidence"] = min(state["confidence"] + 0.05, 0.95)
        
        return state
    
    def _should_enrich(self, state: ExtractionState) -> str:
        """Determine if enrichment step is needed."""
        # Only enrich if confidence is below threshold and no errors
        if state["confidence"] < 0.8 and len(state["errors"]) == 0:
            return "enrich"
        return "end"

