from pydantic import BaseModel, Field
from typing import Optional, List

class ProviderOut(BaseModel):
    provider_id: str
    provider_name: str
    provider_city: Optional[str]
    provider_state: Optional[str]
    provider_zip_code: Optional[str]
    ms_drg_definition: str
    ms_drg_code: Optional[int]
    total_discharges: Optional[int]
    average_covered_charges: Optional[float]
    average_total_payments: Optional[float]
    average_medicare_payments: Optional[float]
    rating_avg: Optional[float] = Field(default=None)
    distance_km: Optional[float] = Field(default=None)

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    data: List[ProviderOut] = []
