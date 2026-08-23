from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.request_models import RecommendationRequest
from app.services.plant_service import load_plants
from app.recommendation_engine import recommend_plants
from app.models.response_models import RecommendationResponse


app = FastAPI(
    title="Biodiversity Native Planting Planner",
    version="1.0.0"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Biodiversity Native Planting Planner!"
    }


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):

    plants = load_plants()

    recommendations = recommend_plants(
    plants,
    request.region,
    request.sunlight,
    request.soil_type,
    request.moisture
    )

    return RecommendationResponse(
    region=request.region,
    sunlight=request.sunlight,
    soil_type=request.soil_type,
    moisture=request.moisture,
    recommendations=recommendations
    )
