from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    region: str
    sunlight: str
    soil_type: str
    moisture: str
