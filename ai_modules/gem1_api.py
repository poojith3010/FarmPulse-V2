import os
import joblib
import json
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

try:
    from local_brain import LocalBrain
except ImportError:
    LocalBrain = None

MODEL_PATH = "models/yield_seasonal_model.joblib"
STATS_PATH = "models/monthly_stats.json"
yield_model = None
monthly_stats = {}
brain = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global yield_model, monthly_stats, brain
    print("🚀 Starting Gem 1: Standardized Yield...")

    if os.path.exists(MODEL_PATH):
        yield_model = joblib.load(MODEL_PATH)
    if os.path.exists(STATS_PATH):
        with open(STATS_PATH, 'r') as f:
            monthly_stats = json.load(f)

    if LocalBrain:
        try: brain = LocalBrain() 
        except: pass
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- NEW INPUT ---
class YieldRequest(BaseModel):
    target_date: str
    farm_size_acres: float = 4.0 # Default to 4 if user is lazy

@app.post("/forecast-yield")
def forecast_yield(data: YieldRequest):
    if not yield_model: return {"error": "Model not loaded."}

    try:
        dt = pd.to_datetime(data.target_date)
        day_of_year = dt.dayofyear
        month_idx = str(dt.month)
        
        # 1. Predict RATE (KG per Acre)
        sin_date = np.sin(2 * np.pi * day_of_year / 365.0)
        cos_date = np.cos(2 * np.pi * day_of_year / 365.0)
        
        predicted_rate_per_acre = float(yield_model.predict(np.array([[sin_date, cos_date]]))[0])
        
        # 2. Scale to User's Farm Size
        total_yield = predicted_rate_per_acre * data.farm_size_acres
        
        # 3. Get Context (Also per acre)
        stats = monthly_stats.get(month_idx, {"mean": predicted_rate_per_acre})
        avg_rate_per_acre = float(stats['mean'])
        
        # 4. AI Explanation
        ai_reply = ""
        if brain:
            formatted_date = dt.strftime("%B %d")
            system_prompt = "You are a Farm Manager. Analyze the yield forecast."
            context = (
                f"Date: {formatted_date}\n"
                f"Farm Size: {data.farm_size_acres} Acres\n"
                f"PREDICTED YIELD: {total_yield:.1f} KG\n"
                f"Productivity Rate: {predicted_rate_per_acre:.1f} KG/Acre\n"
                f"Typical Avg Rate: {avg_rate_per_acre:.1f} KG/Acre"
            )
            ai_reply = brain.generate_response(system_prompt, context, "Is this productivity good?")
            ai_reply = ai_reply.replace("<|im_end|>", "")
        else:
            ai_reply = f"Forecast: {total_yield:.1f} KG ({predicted_rate_per_acre:.1f} KG/Acre)."

        return {
            "predicted_yield_kg": round(total_yield, 2),
            "yield_per_acre": round(predicted_rate_per_acre, 2),
            "reply": ai_reply
        }

    except Exception as e:
        return {"error": str(e)}