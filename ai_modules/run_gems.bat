@echo off
title Agri-Gems Launcher
echo =====================================================
echo 🚀 Starting All Agri-Gems Components
echo    (Assuming 'agni_advisor' is already active)
echo =====================================================

echo.
echo [1/4] Starting Gem 1 (Yield Forecaster)...
start "Gem 1: Yield Forecaster" cmd /k "uvicorn gem1_api:app --port 8004 --reload"

echo.
echo [2/4] Starting Gem 2 (Agri-Researcher)...
start "Gem 2: The Researcher" cmd /k "uvicorn gem2_api:app --port 8001 --reload"

echo.
echo [3/4] Starting Gem 3A (Nutrient Advisor)...
start "Gem 3A: Nutrient Advisor" cmd /k "uvicorn gem3a_api:app --port 8002 --reload"

echo.
echo [4/4] Starting Gem 3B (Vision Doctor)...
start "Gem 3B: Vision Doctor" cmd /k "uvicorn gem3b_api:app --port 8003 --reload"

echo.
echo ✅ All Systems Go!
echo -----------------------------------------------------
echo 📈 Gem 1 (Yield):   http://127.0.0.1:8004
echo 📚 Gem 2 (Guide):   http://127.0.0.1:8001
echo 🩺 Gem 3A (Text):   http://127.0.0.1:8002
echo 👁️ Gem 3B (Vision): http://127.0.0.1:8003
echo -----------------------------------------------------
echo 🌍 Frontend is ready to connect!
pause