import pandas as pd
import numpy as np
import glob
import os
import joblib
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# --- CONFIG ---
DATA_FOLDER = "yield_data"
MODEL_PATH = "models/yield_seasonal_model.joblib"
STATS_PATH = "models/monthly_stats.json"
KNOWN_AREA_ACRES = 4.0  # <--- The Magic Number (Your historical land size)

def train_seasonal_model():
    print(f"📂 Scanning folder: {DATA_FOLDER}...")
    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))
    
    if not all_files:
        print("❌ No files found.")
        return

    df_list = []
    
    for f in all_files:
        try:
            temp_df = pd.read_excel(f)
            temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            
            if 'TOTAL' in temp_df.columns and 'TOTAL WEIGHT' not in temp_df.columns:
                temp_df.rename(columns={'TOTAL': 'TOTAL WEIGHT'}, inplace=True)
            
            if 'DATE' not in temp_df.columns or 'TOTAL WEIGHT' not in temp_df.columns:
                continue

            temp_df['DATE'] = pd.to_datetime(temp_df['DATE'], errors='coerce')
            temp_df = temp_df.dropna(subset=['DATE'])
            temp_df['TOTAL WEIGHT'] = pd.to_numeric(temp_df['TOTAL WEIGHT'], errors='coerce')
            temp_df = temp_df.dropna(subset=['TOTAL WEIGHT'])
            temp_df = temp_df[temp_df['TOTAL WEIGHT'] > 10] 

            # --- STANDARDIZATION ---
            # We convert "Total Yield" to "Yield Per Acre"
            temp_df['YIELD_PER_ACRE'] = temp_df['TOTAL WEIGHT'] / KNOWN_AREA_ACRES
            
            # Features
            temp_df['MONTH'] = temp_df['DATE'].dt.month
            day_of_year = temp_df['DATE'].dt.dayofyear
            temp_df['SIN_DATE'] = np.sin(2 * np.pi * day_of_year / 365.0)
            temp_df['COS_DATE'] = np.cos(2 * np.pi * day_of_year / 365.0)
            
            df_list.append(temp_df[['MONTH', 'SIN_DATE', 'COS_DATE', 'YIELD_PER_ACRE']])
            print(f"✅ Loaded {os.path.basename(f)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    final_df = pd.concat(df_list, ignore_index=True)
    
    # --- CALCULATE PER-ACRE STATS ---
    print("📊 Calculating Per-Acre Benchmarks...")
    stats = final_df.groupby('MONTH')['YIELD_PER_ACRE'].agg(['mean', 'min', 'max']).to_dict('index')
    
    if not os.path.exists("models"): os.makedirs("models")
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f)
    print(f"✅ Stats saved (Values are now in KG/Acre)")

    # --- TRAIN MODEL ---
    X = final_df[['SIN_DATE', 'COS_DATE']]
    y = final_df['YIELD_PER_ACRE'] # <--- Target is now standardized

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    print("🧠 Training Standardized Model...")
    model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"📉 Accuracy (MAE): +/- {mae:.2f} KG per Acre")

    joblib.dump(model, MODEL_PATH)
    print("✅ Model Saved.")

if __name__ == "__main__":
    train_seasonal_model()