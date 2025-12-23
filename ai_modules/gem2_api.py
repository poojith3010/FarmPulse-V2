import json
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import the Unified Brain
from local_brain import LocalBrain

# --- Configuration ---
# We keep these because they contain your Gem 2 data
INDEX_FILE = "faiss.index"
CHUNKS_FILE = "chunks.json"
TOP_K = 3 

# --- Global Variables ---
brain = None
index = None
chunks = None

# --- Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global brain, index, chunks
    print("🚀 Loading Gem 2 (Researcher Mode)...")
    
    try:
        # 1. Load the Unified Brain (LLM + Embedder)
        # This uses the same brain as Gem 3, saving resources!
        brain = LocalBrain()
        
        # 2. Load Gem 2 Specific Knowledge (FAISS + Text Chunks)
        print(f"📂 Loading Knowledge Base from {INDEX_FILE}...")
        index = faiss.read_index(INDEX_FILE)
        
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        print("✅ Gem 2 Ready! Connected to Offline AI.")
    except Exception as e:
        print(f"❌ Error starting Gem 2: {e}")
    
    yield
    print("🛑 Shutting down Gem 2...")

# --- FastAPI App ---
app = FastAPI(
    lifespan=lifespan,
    title="Agri-Gems AI Advisor",
    description="API for the 'Agri-Advisor' (Gem 2) using Unified LocalBrain"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Query(BaseModel):
    question: str

# --- Helper Functions ---

def find_relevant_chunks(question_text: str):
    """
    Uses the Brain's embedder to search the FAISS index.
    """
    # 1. Encode the user's question using the Brain's embedder
    # We don't need to load a separate model!
    query_vector = brain.embedder.encode([question_text], convert_to_tensor=False)
    
    # 2. Search the FAISS index
    distances, indices = index.search(query_vector.astype('float32'), TOP_K)
    
    # 3. Retrieve the actual text chunks
    relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
    
    return relevant_chunks

# --- API Endpoints ---

@app.get("/")
def get_root():
    return {"message": "Agri-Advisor (Gem 2) is running via LocalBrain!"}

@app.post("/ask-advisor")
def ask_question(query: Query):
    """
    Receives a question -> Finds Manual Pages -> Generates Friendly Answer.
    """
    if not brain or not index:
        raise HTTPException(status_code=500, detail="System not fully loaded.")

    # 1. Retrieve Context (The "Librarian" Work)
    relevant_chunks = find_relevant_chunks(query.question)
    
    # Combine chunks into a single string
    context_text = "\n\n".join(relevant_chunks)
    
    # 2. Generate Answer (The "Writer" Work)
    system_instruction = (
        "You are an expert Agricultural Advisor. "
        "Use the 'Context' provided below (which comes from technical manuals) to answer the user's question. "
        "If the context has the answer, explain it clearly and professionally to the farmer. "
        "If the context is unrelated or empty, politely say you don't find that in the manuals."
        "Answer the user's question concisely in under 100 words."
    )
    
    # Use the unified brain to generate the response
    ai_answer = brain.generate_response(
        system_instructions=system_instruction,
        context_data=context_text,
        user_query=query.question
    )
    
    return {
        "question": query.question,
        "answer": ai_answer, # The friendly AI text
        "source_context": relevant_chunks # Debug: Show what it read
    }