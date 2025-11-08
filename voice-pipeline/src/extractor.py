import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define the structured schema
class CRMData(BaseModel):
    contact_name: str | None = Field(None, description="Name of the contact person")
    company: str | None = Field(None, description="Name of the company")
    next_step: str | None = Field(None, description="Next action item or meeting")
    deal_value: str | None = Field(None, description="Potential deal value")
    follow_up_date: str | None = Field(None, description="Date for follow-up, if mentioned")
    notes: str | None = Field(None, description="Additional context or details")

def extract_crm_fields(transcript: str) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0
    )

    parser = PydanticOutputParser(pydantic_object=CRMData)

    prompt = PromptTemplate(
        input_variables=["conversation"],
        template=(
            "Extract the following fields from this sales conversation:\n"
            "- contact name\n- company\n- next step\n- deal value\n- follow-up date\n- notes\n\n"
            "Conversation:\n{conversation}\n\n"
            "Return output that matches this JSON schema:\n{format_instructions}"
        ),
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser
    result = chain.invoke({"conversation": transcript})
    return result.dict()
