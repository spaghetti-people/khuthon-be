from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
from app.utils.predict import preprocess_data, normalize_prediction
import joblib
from pathlib import Path

router = APIRouter()

# 모델 경로
model_path = Path(__file__).parent.parent / "utils" / "models" / "crop_growth_model.pkl"
if not model_path.exists():
    raise RuntimeError("모델 파일을 찾을 수 없습니다.")
model = joblib.load(model_path)


class SensorData(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
    soil_moisture: float
    soil_type: int
    sunlight_exposure: float
    wind_speed: float
    co2_concentration: float
    organic_matter: float
    irrigation_frequency: int
    crop_density: float
    pest_pressure: float
    fertilizer_usage: float
    growth_stage: int
    urban_area_proximity: float
    water_source_type: int
    frost_risk: float
    water_usage_efficiency: float


class PredictionResponse(BaseModel):
    growth_potential: float
    evaluation: str


@router.post("/predict", response_model=PredictionResponse)
def predict_growth(sensor_data: SensorData):
    try:
        input_data = pd.DataFrame([sensor_data.dict()])
        processed_data = preprocess_data(input_data)
        prediction = model.predict(processed_data)[0]
        normalized_prediction = normalize_prediction(prediction)
        if normalized_prediction >= 80:
            evaluation = "매우 좋음"
        elif normalized_prediction >= 60:
            evaluation = "좋음"
        elif normalized_prediction >= 40:
            evaluation = "보통"
        elif normalized_prediction >= 20:
            evaluation = "나쁨"
        else:
            evaluation = "매우 나쁨"
        return PredictionResponse(
            growth_potential=float(normalized_prediction), evaluation=evaluation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 처리 중 오류: {str(e)}")
