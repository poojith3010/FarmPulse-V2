# Agri-Gems: AI-Powered Agricultural Assistance Platform

## Overview

Agri-Gems is a modular, AI-powered platform designed to provide a suite of tools for modern farming. It operates as a collection of specialized microservices, or "Gems," each tackling a specific agricultural challenge. The system is designed for local, offline-first operation, leveraging a local Large Language Model (LLM) and a vector database to ensure functionality without constant internet access. A simple web-based frontend provides a user-friendly interface to interact with the various AI modules.

## Features

*   **Yield Forecasting:** Predicts seasonal crop yield based on farm size and time of year.
*   **AI-Powered Research:** Answers agricultural questions using a local knowledge base.
*   **Plant Nutrient & pH Diagnosis:** Analyzes real-time sensor data to diagnose soil health issues.
*   **Visual Plant Disease Detection:** Identifies plant diseases from uploaded leaf images.
*   **Modular Microservice Architecture:** Each feature is an independent API, allowing for flexibility and scalability.
*   **Local First:** Core AI models run locally, reducing reliance on cloud services.

## Architecture

The project follows a microservice architecture where each "Gem" is a self-contained FastAPI application. A central module, `local_brain.py`, is the core of the system's intelligence. It loads a sentence-transformer model (`all-MiniLM-L6-v2`) and a local LLM (`llm.gguf`) into memory once. All other Gem APIs utilize this shared instance, which prevents redundant model loading and conserves system resources (GPU/CPU).

The `run_gems.bat` script launches all the FastAPI services simultaneously, making them available on different local ports.

---

## Modules (The "Gems")

### 💎 Gem 1: Yield Forecaster
*   **API Endpoint:** `http://localhost:8004`
*   **Functionality:** Predicts seasonal crop yield. It takes a target date and farm size (in acres) as input.
*   **Technology:** Uses a Scikit-learn machine learning model (`yield_seasonal_model.joblib`) for prediction and integrates with the `local_brain` to provide conversational, context-aware explanations for the forecast.

### 💎 Gem 2: Agri-Researcher
*   **API Endpoint:** `http://localhost:8001`
*   **Functionality:** A Retrieval-Augmented Generation (RAG) based research assistant. Users can ask questions in natural language, and the system provides answers based on a local knowledge base built from documents in the `knowledge_base` folder.
*   **Technology:** It uses a FAISS vector index (`faiss.index`) for efficient similarity search and the `local_brain` to synthesize answers from the retrieved text chunks.

### 💎 Gem 3A: Nutrient Advisor
*   **API Endpoint:** `http://localhost:8002`
*   **Functionality:** A "Plant Doctor" that diagnoses soil nutrient and pH issues by connecting to live sensor data stored in a Supabase database.
*   **Technology:** It fetches sensor data, evaluates it against predefined rules in `crop_rules.json`, and uses the `local_brain` to deliver a user-friendly diagnosis and recommendation.

### 💎 Gem 3B: Vision Doctor
*   **API Endpoint:** `http://localhost:8003`
*   **Functionality:** Analyzes user-uploaded images of plant leaves to identify diseases or confirm health.
*   **Technology:** It uses a PyTorch deep learning model (`plant_doctor_vision.pth`) for image classification. Upon identifying a disease, it retrieves detailed information from `disease_info.json` and uses the `local_brain` to compose a "doctor's note" explaining the symptoms and control methods.

---

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+
    *   A C++ compiler (required for `ctransformers`)
    *   CUDA-enabled GPU (recommended for better performance with the local LLM)

2.  **Virtual Environment:**
    The project includes a pre-configured virtual environment in the `multimodal_env` directory. To activate it, run:
    ```bash
    # On Windows
    .\multimodal_env\Scripts\activate
    ```

3.  **Install Dependencies:**
    Once the virtual environment is activated, install the required Python packages using the `requirements.txt` file from the root project directory.
    ```bash
    pip install -r ..\requirements.txt
    ```

4.  **LLM Model:**
    This project requires a Large Language Model in GGUF format. Place the model file in the `ai_modules` directory and name it `llm.gguf`.

---

## Usage

1.  **Run the Services:**
    Execute the `run_gems.bat` script to start all the AI microservices. This will open multiple terminal windows, one for each Gem.
    ```bash
    run_gems.bat
    ```

2.  **Access the Frontend:**
    Open the `index.html` file located in the `frontend` directory in your web browser. This interface allows you to interact with all the available Gems.

---

## Training and Data

The project includes scripts for training the AI models and processing data.

*   **`build_index.py`:**
    This script builds the vector database for the Agri-Researcher (Gem 2). It reads text files from the `knowledge_base` directory, splits them into chunks, generates embeddings, and saves them to the `faiss.index` file.

*   **`train_vision.py`:**
    This script trains the computer vision model for the Vision Doctor (Gem 3B). It uses images from the `dataset` folder, applies transfer learning on a MobileNetV2 architecture, and saves the trained model as `plant_doctor_vision.pth`.

## File Structure

```
ai_modules/
│
├── frontend/             # Web interface files
├── knowledge_base/       # Text documents for the RAG model
├── models/               # Trained AI/ML models
├── dataset/              # Image dataset for vision model training
│
├── build_index.py        # Script to build the FAISS index
├── train_vision.py       # Script to train the vision model
│
├── gem1_api.py           # Yield Forecaster API
├── gem2_api.py           # Agri-Researcher API
├── gem3a_api.py          # Nutrient Advisor API
├── gem3b_api.py          # Vision Doctor API
│
├── local_brain.py        # Central module for loading and sharing AI models
├── run_gems.bat          # Batch script to launch all services
│
├── llm.gguf              # Local Large Language Model (user-provided)
└── ...                   # Other configuration and data files
```
