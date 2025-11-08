"""FastAPI application for CRM parsing services."""
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import InteractionEvent, ParsingResponse, ExtractedData
from services.preprocessing import PreprocessingService
from services.extraction import ExtractionService
from services.bigquery_storage import BigQueryStorage
from config import settings

app = FastAPI(title="CRM AI Agent - Parsing Services", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
preprocessing_service = PreprocessingService()
extraction_service = ExtractionService()
storage_service = BigQueryStorage()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "crm-parsing"}


@app.post("/parse", response_model=ParsingResponse)
async def parse_interaction(event: InteractionEvent):
    """
    Main parsing endpoint.
    
    Processes an interaction event:
    1. Preprocesses (normalize, transcribe audio if needed)
    2. Extracts structured data using LangGraph
    3. Saves to BigQuery
    """
    try:
        # Step 1: Preprocess
        processed_event = await preprocessing_service.process_event(event)
        
        # Step 2: Extract structured data
        extracted_data, confidence, processing_time_ms = await extraction_service.extract(
            processed_event
        )
        
        # Step 3: Save to BigQuery
        interaction_id = await storage_service.save_interaction(
            processed_event=processed_event,
            extracted_data=extracted_data,
            confidence=confidence,
        )
        
        return ParsingResponse(
            interaction_id=interaction_id,
            extracted_data=extracted_data,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/preprocess")
async def preprocess_only(event: InteractionEvent):
    """Preprocess an event without extraction (for testing)."""
    try:
        processed = await preprocessing_service.process_event(event)
        return {
            "raw_text": processed.raw_text,
            "transcript": processed.transcript,
            "language": processed.language,
            "channel": processed.channel.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preprocessing error: {str(e)}")


@app.post("/extract")
async def extract_only(processed_event: dict):
    """Extract data from a processed event (for testing)."""
    try:
        from models.schemas import ProcessedEvent
        event = ProcessedEvent(**processed_event)
        extracted_data, confidence, processing_time_ms = await extraction_service.extract(event)
        
        return {
            "extracted_data": extracted_data.model_dump(),
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

