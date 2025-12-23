import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Import Config
from db_config import TABLE_SENSORS, SENSOR_COLS, map_sensor_data

try:
    from local_brain import LocalBrain
except ImportError:
    LocalBrain = None

load_dotenv()

brain = None
supabase = None
RULES = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global brain, supabase, RULES
    try:
        with open('crop_rules.json', 'r') as f:
            RULES = json.load(f)
        print("✅ Rules loaded.")
    except Exception as e:
        print(f"❌ Error loading rules: {e}")

    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)
        print("✅ Supabase connected.")
    except Exception as e:
        print(f"❌ Supabase Error: {e}")
    
    if LocalBrain:
        try:
            brain = LocalBrain()
            print("✅ AI Brain Connected.")
        except:
            brain = None
    yield
    print("🛑 Shutting down...")

app = FastAPI(lifespan=lifespan, title="Plant Doctor AI (Offline)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW INPUT MODEL ---
class UserQuery(BaseModel):
    query_text: str
    mac_address: str = "DEMO_DEVICE" # Default for testing if frontend forgets

# --- LOGIC ENGINE ---
def evaluate_nutrient_needs(current_growth_stage, sensor_readings, rules_data):
    active_alerts = []
    for rule in rules_data['rule_set']:
        conditions = rule['conditions']
        if conditions.get('crop') and 'tea' not in conditions['crop'].lower(): continue
        if 'growth_stage_any_of' in conditions:
            if current_growth_stage not in conditions['growth_stage_any_of']: continue 

        rule_triggered = False 
        if 'sensor' in conditions:
            sensor_conditions = conditions['sensor']
            for metric, checks in sensor_conditions.items():
                if metric in sensor_readings:
                    actual_value = sensor_readings[metric]
                    if 'less_than_or_equal_to' in checks and actual_value <= checks['less_than_or_equal_to']: rule_triggered = True
                    elif 'less_than' in checks and 'or_greater_than' not in checks and actual_value < checks['less_than']: rule_triggered = True
                    elif 'less_than' in checks and 'or_greater_than' in checks:
                        if actual_value < checks['less_than'] or actual_value > checks['or_greater_than']: rule_triggered = True
                            
        if rule_triggered:
            template = rule['action_template']
            stage_info = rules_data['nutrient_targets_by_growth_stage']['growth_stages'].get(current_growth_stage, {})
            targets = stage_info.get('recommended_annual_dose_kg_per_ha', {})
            response = template.format(
                crop=rules_data['metadata']['crop'], growth_stage=current_growth_stage,
                live_N=sensor_readings.get('soil_nitrogen_ppm_or_kg_per_ha', 'N/A'),
                live_P=sensor_readings.get('available_P2O5_kg_per_ha', 'N/A'),
                live_K=sensor_readings.get('available_K2O_kg_per_ha', 'N/A'),
                live_pH=sensor_readings.get('soil_pH', 'N/A'), units="kg/ha", 
                target_N=targets.get('N', '?'), target_P=targets.get('P2O5', '?'), target_K=targets.get('K2O', '?'),
                target_units="kg/ha", suggested_N_rate_kg_per_ha=100, latest_lab_date="2024-10-01"
            )
            active_alerts.append(response)

    if active_alerts: return "\n\n".join(active_alerts)
    return rules_data['response_templates_and_placeholders']['recommendation_style_guidelines']['example_no_response']

# --- HELPER ---
def get_live_data(target_mac):
    try:
        # SECURE QUERY
        response = supabase.table(TABLE_SENSORS) \
            .select("*") \
            .eq(SENSOR_COLS["MAC_ADDRESS"], target_mac) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"DB Error: {e}")
        return None

# --- API ENDPOINT ---
@app.post("/ask")
def ask_plant_doctor(query: UserQuery):
    user_text = query.query_text
    user_mac = query.mac_address 
    
    possible_intents = {
        "check_nutrients": "Check fertilizer, NPK, nitrogen, phosphorus, soil food, hungry plants",
        "check_ph": "Check soil acidity, alkalinity, pH level, soil health",
        "greeting": "Hello, hi, who are you, what can you do",
        "unknown": "weather, rain, market price, random stuff"
    }
    
    if not brain: return {"reply": "System Error: AI Brain not loaded."}

    intent, score = brain.find_intent(user_text, possible_intents)
    print(f"🧠 Analysis: Intent='{intent}' (Score: {score:.2f})")
    
    if score < 0.25 or intent == "unknown":
        return {"reply": "I am strictly a Nutrient Advisor. Please ask me about fertilizer, pH, or soil health."}

    if intent == "greeting":
        return {"reply": "Hello! I am your AI Plant Doctor. I am connected to your specific sensor unit. Ask me: 'Does my plot need fertilizer?'"}

    # 3. EXECUTE LOGIC
    raw_data = get_live_data(user_mac)
    
    if not raw_data: 
        return {"reply": f"I cannot find any sensor data for Device ID: {user_mac}. Please ensure your device is online."}

    clean_data = map_sensor_data(raw_data)

    mapped_readings = {
        "soil_nitrogen_ppm_or_kg_per_ha": clean_data['nitrogen'],
        "available_P2O5_kg_per_ha": clean_data['phosphorus'],
        "available_K2O_kg_per_ha": clean_data['potassium'],
        "soil_pH": clean_data['ph']
    }
    
    # Run the Rules (Get the bad news)
    technical_advice = evaluate_nutrient_needs("high_demand_plucking_flush", mapped_readings, RULES)
    
    # 4. GENERATIVE REWRITE (IMPROVED CONTEXT)
    # We explicitly separate "Facts" from "Problems" so the AI sees everything.
    
    system_prompt = (
        "You are an expert Agronomist. "
        "Your task: Answer the User Question based strictly on the Sensor Report below. "
        "LOGIC RULES:"
        "1. Look at the 'CURRENT VALUES'. Tell the user the specific number they asked about."
        "2. Check 'ACTIVE ALERTS'. If the nutrient is listed there, give the recommendation."
        "3. SANITY CHECK: If a nutrient value is exactly 0 or 0.0, do NOT say it is healthy. "
        "Instead, warn the user that the sensor might be disconnected or the soil is completely depleted."
        "4. If the nutrient is > 0 AND not in 'ACTIVE ALERTS', explicitly state that it is HEALTHY and SAFE."
        "5. Do NOT talk about pH unless the user asks for it or it is in the Alerts."
    )
    
    context = f"""
    USER QUESTION: "{user_text}"

    CURRENT VALUES (Live Sensor Data):
    - Nitrogen: {clean_data['nitrogen']} kg/ha
    - Phosphorus: {clean_data['phosphorus']} kg/ha
    - Potassium: {clean_data['potassium']} kg/ha
    - pH: {clean_data['ph']}

    ACTIVE ALERTS (Problems detected by Logic Engine):
    {technical_advice if technical_advice else "None - All levels optimal."}
    """
    
    ai_response = brain.generate_response(system_prompt, context, user_text)
    
    return {
        "intent": intent,
        "technical_rule": technical_advice,
        "reply": ai_response.replace("<|im_end|>", "")
    }