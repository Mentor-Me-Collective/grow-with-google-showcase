from pydantic import BaseModel

class PlantRecommendation(BaseModel):
    species_id: str
    common_name: str
    scientific_name: str
    native_range: str
    bloom_start: str
    bloom_end: str
    sun_needs: str
    soil_type: str
    moisture: str
    pollinators_supported: list[str]
    hardiness_zones: str
    source: str
    source_url: str
    score: int

class RecommendationResponse(BaseModel):
    region: str
    sunlight: str
    soil_type: str
    moisture: str
    recommendations: list[PlantRecommendation]