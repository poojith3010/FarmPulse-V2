import pandas as pd
import glob
import os

DATA_FOLDER = "yield_data"

print("🔍 Inspecting Excel Headers...")
files = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))

for f in files:
    try:
        df = pd.read_excel(f)
        # Show us exactly what the computer sees (Uppercase & Stripped)
        clean_cols = [str(c).strip().upper() for c in df.columns]
        
        print(f"\n📄 File: {os.path.basename(f)}")
        print(f"   👉 Found: {clean_cols}")
        
        # specific check
        has_date = 'DATE' in clean_cols
        has_weight = 'TOTAL WEIGHT' in clean_cols
        
        if not has_date:
            print("   ❌ Missing 'DATE'")
        if not has_weight:
            print("   ❌ Missing 'TOTAL WEIGHT'")
            
    except Exception as e:
        print(f"❌ Error reading {os.path.basename(f)}: {e}")

input("\nPress Enter to exit...")