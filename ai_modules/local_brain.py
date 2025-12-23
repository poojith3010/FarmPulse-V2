from gpt4all import GPT4All
from sentence_transformers import SentenceTransformer, util
import os

class LocalBrain:
    def __init__(self):
        print("🧠 Initializing Local Brain (GPT4All Edition)...")
        
        # 1. LOAD THE LIBRARIAN (MiniLM)
        print("📚 Loading Librarian...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
        
        # 2. LOAD THE WRITER (Your GGUF File)
        # Ensure this matches your actual filename
        model_filename = "llm.gguf"
        
        # Check if file exists in current directory
        if not os.path.exists(model_filename):
            raise FileNotFoundError(f"❌ Model file '{model_filename}' not found in the current folder.")
            
        print(f"✍️  Loading Writer from current folder: {model_filename}...")
        
        # Load the model
        self.llm = GPT4All(model_filename, model_path=".", allow_download=False, device='cuda:NVIDIA GeForce RTX 4070 Laptop GPU')
        
        print("✅ Local Brain Ready!")

    def find_intent(self, user_query, predefined_intents):
        """
        Uses MiniLM to find which 'tool' matches the user's question.
        """
        query_embedding = self.embedder.encode(user_query, convert_to_tensor=True)
        
        intent_names = list(predefined_intents.keys())
        intent_descriptions = list(predefined_intents.values())
        
        desc_embeddings = self.embedder.encode(intent_descriptions, convert_to_tensor=True)
        
        hits = util.semantic_search(query_embedding, desc_embeddings, top_k=1)
        best_hit = hits[0][0]
        
        score = best_hit['score']
        best_intent = intent_names[best_hit['corpus_id']]
        
        return best_intent, score

    def generate_response(self, system_instructions, context_data, user_query):
        """
        Uses your GGUF model to write a response via GPT4All.
        """
        # Prompt format optimized for Qwen/Instruct models
        prompt = f"""<|im_start|>system
{system_instructions}
<|im_end|>
<|im_start|>user
Context Information:
---------------------
{context_data}
---------------------

Question: {user_query}
<|im_end|>
<|im_start|>assistant
"""
        
        # Generate response
        # We use temp=0.1 for factual, steady answers
        response = self.llm.generate(prompt, max_tokens=600, temp=0.1)
            
        return response

# Test block
if __name__ == "__main__":
    brain = LocalBrain()
    print(brain.generate_response("You are helpful.", "Data: N=0", "Is my plant hungry?"))