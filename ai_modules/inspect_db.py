import os
import json
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY missing from .env")
    exit()

# Initialize Client
supabase: Client = create_client(URL, KEY)

def list_all_tables():
    """
    Uses the REST API to find all table names.
    """
    print(f"\n🔍 Scanning Supabase at: {URL} ...")
    
    api_url = f"{URL}/rest/v1/"
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            definitions = response.json().get('definitions', {})
            print("\n--- 📂 EXISTING TABLES ---")
            for table_name in definitions.keys():
                print(f"  - {table_name}")
            print("--------------------------")
            return list(definitions.keys())
        else:
            print(f"⚠️ Could not list tables via REST (Status: {response.status_code})")
            return []
    except Exception as e:
        print(f"❌ Error scanning tables: {e}")
        return []

def inspect_table_structure(table_name):
    """
    Fetches 1 row to determine column names and data types.
    """
    print(f"\n🔬 Inspecting structure of table: '{table_name}'...")
    
    try:
        # Fetch 1 row
        response = supabase.table(table_name).select("*").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            first_row = response.data[0]
            columns = list(first_row.keys())
            
            print(f"   ✅ Connection Successful. Found {len(columns)} columns.")
            print("\n   --- 📝 COLUMN MAPPING ---")
            for col in columns:
                # Print column name and the type of data inside (int, float, str)
                example_val = first_row[col]
                val_type = type(example_val).__name__
                print(f"   Column: '{col}' \t(Type: {val_type}) \tExample: {example_val}")
            print("   -------------------------")
            
            return columns
        else:
            print(f"   ⚠️ Table '{table_name}' is empty. Cannot determine columns.")
            return []

    except Exception as e:
        print(f"   ❌ Error inspecting {table_name}: {e}")
        return []

if __name__ == "__main__":
    # 1. List all
    tables = list_all_tables()
    
    # 2. Specifically inspect the 'sensor_data' table (Crucial for Gem 1 & 3A)
    target_table = "sensor_data"
    if target_table in tables:
        cols = inspect_table_structure(target_table)
    else:
        # Fallback if REST failed but we know the name
        inspect_table_structure(target_table)