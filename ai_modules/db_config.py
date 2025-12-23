# db_config.py

# --- TABLE CONFIG ---
TABLE_SENSORS = "sensor_data"

# --- COLUMN MAPPING ---
# Left Side: Our Python Name (Clean)
# Right Side: Your Database Column Name (Dirty)
SENSOR_COLS = {
    "NITROGEN": "nitrogen",
    "PHOSPHORUS": "phosphorus",
    "POTASSIUM": "potassium",
    "TEMPERATURE": "temperature",
    "HUMIDITY": "humidity",
    "RAINFALL": "rain_value",
    "MOISTURE": "soil_moisture",
    "PH": "ph_value",
    "TIMESTAMP": "created_at",
    
    # NEW: The Security Key
    # If your column is named 'device_id' or 'station_mac', CHANGE THIS VALUE:
    "MAC_ADDRESS": "mac_address" 
}

# --- DATA MAPPER ---
def map_sensor_data(db_row):
    """
    Converts a raw Supabase row into a clean dictionary.
    """
    if not db_row:
        return None
        
    return {
        "nitrogen": float(db_row.get(SENSOR_COLS["NITROGEN"], 0)),
        "phosphorus": float(db_row.get(SENSOR_COLS["PHOSPHORUS"], 0)),
        "potassium": float(db_row.get(SENSOR_COLS["POTASSIUM"], 0)),
        "temperature": float(db_row.get(SENSOR_COLS["TEMPERATURE"], 25.0)),
        "rainfall": float(db_row.get(SENSOR_COLS["RAINFALL"], 1500.0)),
        "humidity": float(db_row.get(SENSOR_COLS["HUMIDITY"], 70.0)),
        "ph": float(db_row.get(SENSOR_COLS["PH"], 5.5)), 
        "moisture": float(db_row.get(SENSOR_COLS["MOISTURE"], 30.0)),
        "timestamp": db_row.get(SENSOR_COLS["TIMESTAMP"], "")
    }