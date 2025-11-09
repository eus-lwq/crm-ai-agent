from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Schema 
class CRMData(BaseModel):
    contact_name: str | None = Field(None, description="Name of the contact person")
    company: str | None = Field(None, description="Company name")
    next_step: str | None = Field(None, description="Next step or action")
    deal_value: str | None = Field(None, description="Potential deal value")
    follow_up_date: str | None = Field(None, description="Follow-up date if mentioned")
    notes: str | None = Field(None, description="Additional context or details")
    interaction_medium: str = Field("phone_call", description="Mode of communication (always 'phone_call')")

# Gemini Call
def extract_crm_fields(transcript: str) -> dict:
    """
    Uses Gemini 2.0 Flash model on Vertex AI to extract structured CRM data
    from a sales conversation transcript.
    """

    client = genai.Client(vertexai=True)
    model = "gemini-2.0-flash-lite-001"

    # prompt
    prompt = f"""
    Extract the following CRM fields from this sales conversation:
    - contact name
    - company
    - next step
    - deal value
    - follow-up date
    - notes

    Conversation:
    {transcript}
    """

    response = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CRMData.model_json_schema(),
        ),
    )

    crm = CRMData.model_validate_json(response.text)

    crm.interaction_medium = "phone_call"

    print("Parsed CRM data:", crm.dict())
    return crm.dict()
