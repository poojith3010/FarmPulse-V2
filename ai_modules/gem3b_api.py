import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms
import io
import json
from contextlib import asynccontextmanager

# Import the Unified Brain
from local_brain import LocalBrain

# --- CONFIGURATION ---
MODEL_PATH = "models/plant_doctor_vision.pth"
CLASS_NAMES_PATH = "models/plant_doctor_vision_classes.txt"
DISEASE_INFO_PATH = "disease_info.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- GLOBAL VARIABLES ---
vision_model = None
class_names = []
disease_info = {}
brain = None

# --- LIFECYCLE MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global vision_model, class_names, disease_info, brain
    print("🚀 Starting Gem 3B (Vision + AI Doctor)...")
    
    try:
        # 1. Load Vision Model
        vision_model = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
        vision_model.eval()
        print("✅ Vision Model Loaded.")
        
        # 2. Load Class Names
        with open(CLASS_NAMES_PATH, "r") as f:
            class_names = [line.strip() for line in f.readlines()]
            
        # 3. Load Disease Medical Guide (JSON)
        with open(DISEASE_INFO_PATH, "r") as f:
            disease_info = json.load(f)
            
        # 4. Load the AI Brain (LLM) for the "Personality"
        # (If it's already loaded by another Gem, this uses the same GPU memory if handled correctly, 
        # but for safety in independent testing, we initialize it here).
        brain = LocalBrain()
        print("✅ AI Brain Connected.")
        
    except Exception as e:
        print(f"❌ Error loading resources: {e}")
    
    yield
    print("🛑 Shutting down Gem 3B...")

app = FastAPI(lifespan=lifespan, title="Gem 3B: AI Plant Doctor")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- PREPROCESSING ---
def transform_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    my_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return my_transforms(image).unsqueeze(0).to(DEVICE)

# --- ENDPOINT ---
@app.post("/analyze-leaf")
async def analyze_leaf(file: UploadFile = File(...)):
    if not vision_model:
        return {"error": "System not ready"}
    
    # 1. Vision Prediction
    image_bytes = await file.read()
    tensor = transform_image(image_bytes)
    
    with torch.no_grad():
        outputs = vision_model(tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        top_prob, top_idx = torch.max(probabilities, 1)
        
        confidence = top_prob.item() * 100
        predicted_key = class_names[top_idx.item()] # e.g., "algal_leaf"
        
    # 2. Retrieve Medical Facts (JSON)
    # Fallback to "Unknown" if the model predicts a class not in our JSON
    facts = disease_info.get(predicted_key, {
        "name": predicted_key,
        "symptoms": "Unknown",
        "organic_control": "Consult an expert.",
        "chemical_control": "Consult an expert."
    })
    
    # 3. Generate AI Doctor's Note (The "Wrapper")
    # We feed the strict facts to the LLM to make them sound natural.
    
    system_prompt = (
        "You are an expert Plant Pathologist. "
        "You have just analyzed a tea leaf image. "
        "Use the 'Medical Facts' provided below to explain the diagnosis to the farmer. "
        "Be helpful, empathetic, and practical. Do not invent new treatments."
    )
    
    context_data = f"""
    Diagnosis: {facts['name']}
    Confidence: {confidence:.1f}%
    Symptoms: {facts['symptoms']}
    Organic Treatment: {facts['organic_control']}
    Chemical Treatment: {facts['chemical_control']}
    """
    
    # Call the LLM
    ai_advice = brain.generate_response(system_prompt, context_data, "What is wrong with my plant and how do I fix it?")

    return {
        "filename": file.filename,
        "prediction": facts['name'],
        "confidence": f"{confidence:.2f}%",
        "technical_facts": facts, # Returning the raw JSON for the UI to display if needed
        "doctor_note": ai_advice # The natural language explanation
    }