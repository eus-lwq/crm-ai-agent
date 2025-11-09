"""Pydantic schemas for email extraction."""
from typing import Optional
from pydantic import BaseModel, Field

try:
    from pydantic.v1 import BaseModel as V1BaseModel, Field as V1Field
except ImportError:
    V1BaseModel = BaseModel
    V1Field = Field


class EmailCRMData(BaseModel):
    """Structured CRM data extracted from emails."""
    contact_name: Optional[str] = Field(None, description="Name of the contact person mentioned in the email")
    company: Optional[str] = Field(None, description="Name of the company mentioned in the email")
    next_step: Optional[str] = Field(None, description="Next action item or meeting mentioned")
    deal_value: Optional[str] = Field(None, description="Potential deal value mentioned (e.g., '$75,000', '50k')")
    follow_up_date: Optional[str] = Field(None, description="Date for follow-up if mentioned (any format)")
    notes: Optional[str] = Field(None, description="Additional context, important details, or notes from the email")

