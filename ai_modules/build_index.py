import pathlib
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# --- Configuration ---
KB_PATH = pathlib.Path("knowledge_base")
MODEL_NAME = "all-MiniLM-L6-v2" # A fast, popular model
INDEX_FILE = "faiss.index"      # The file our "brain" will be saved to
CHUNKS_FILE = "chunks.json"     # A file to store the text chunks

# Text Chunking Parameters
# We split docs into 5-sentence chunks, with a 2-sentence overlap
CHUNK_SIZE = 5 
CHUNK_OVERLAP = 2
# ---------------------

def read_text_from_kb() -> list[str]:
    """
    Reads all .txt files in the KB_PATH and splits them into
    smaller, overlapping chunks of text.
    """
    print("Reading text from .txt files...")
    all_texts = []
    
    # Read text from all .txt files
    for txt_file in KB_PATH.glob("*.txt"):
        with open(txt_file, "r", encoding="utf-8") as f:
            all_texts.append(f.read())
            
    # Combine into one big text block
    full_text = "\n".join(all_texts)
    
    # Split the text into individual sentences
    # This is a simple split, better libraries (like NLTK) exist
    # but for TNAU guides, this is usually good enough.
    sentences = full_text.split(".") 
    
    # Clean up (remove empty sentences and extra whitespace)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    print(f"Total sentences found: {len(sentences)}")

    # --- Create Overlapping Chunks ---
    # Now, group sentences into overlapping chunks
    text_chunks = []
    for i in range(0, len(sentences) - CHUNK_SIZE + 1, CHUNK_SIZE - CHUNK_OVERLAP):
        # Get CHUNK_SIZE sentences
        chunk = ". ".join(sentences[i : i + CHUNK_SIZE]) + "."
        text_chunks.append(chunk)
        
    print(f"Total text chunks created: {len(text_chunks)}")
    
    # Save the chunks to a file so our API can retrieve them later
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f)
    
    print(f"Text chunks saved to {CHUNKS_FILE}")
    return text_chunks

def build_faiss_index(chunks: list[str]):
    """
    Converts text chunks into vectors and builds the FAISS index.
    """
    print(f"Loading sentence transformer model: {MODEL_NAME}...")
    # 1. Load the AI model
    # This will download the model the first time you run it
    model = SentenceTransformer(MODEL_NAME)
    
    print("Model loaded. Encoding text chunks (this may take a moment)...")
    
    # 2. Convert all text chunks into vector embeddings
    # The 'model.encode' function turns our list of strings into a 
    # big list of numbers (a numpy array).
    embeddings = model.encode(chunks, show_progress_bar=True)
    
    print(f"Encoding complete. Vector dimension: {embeddings.shape[1]}")
    
    # 3. Create the FAISS index
    # We are using a simple 'IndexFlatL2', which is a good default.
    # It stores the vectors and allows us to search them.
    index = faiss.IndexFlatL2(embeddings.shape[1])
    
    # 4. Add our vectors to the index
    index.add(embeddings.astype('float32')) # FAISS requires float32
    
    print(f"FAISS index created. Total vectors in index: {index.ntotal}")
    
    # 5. Save the index to disk
    faiss.write_index(index, INDEX_FILE)
    print(f"Index successfully saved to: {INDEX_FILE}")


if __name__ == "__main__":
    text_chunks = read_text_from_kb()
    if text_chunks:
        build_faiss_index(text_chunks)
    else:
        print("No text chunks were found. Did you add .txt files to the knowledge_base?")