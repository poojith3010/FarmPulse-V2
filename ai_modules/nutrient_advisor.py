import json

# --- 1. LOAD THE RULES ---
def load_rules(filename='crop_rules.json'):
    with open(filename, 'r') as f:
        return json.load(f)

# --- 2. THE LOGIC ENGINE ---
def evaluate_nutrient_needs(current_growth_stage, sensor_readings, rules_data):
    """
    Compares sensor data against the simplified Single-Plot JSON rules.
    """
    
    # We don't need to look up plot_ids anymore. We assume 'main_plot'.
    # We just need to match the current growth stage and sensor values.

    # Iterate through the rules defined in the JSON
    for rule in rules_data['rule_set']:
        conditions = rule['conditions']
        
        # A. CHECK CROP (Safety check: verify the rule applies to Tea)
        if conditions.get('crop') and 'tea' not in conditions['crop'].lower():
            continue

        # B. CHECK GROWTH STAGE
        # The rule might apply to specific stages only (e.g., flowering)
        if 'growth_stage_any_of' in conditions:
            if current_growth_stage not in conditions['growth_stage_any_of']:
                continue # Rule doesn't apply to this stage

        # C. CHECK SENSOR VALUES
        rule_triggered = False 
        
        if 'sensor' in conditions:
            sensor_conditions = conditions['sensor']
            
            for metric, checks in sensor_conditions.items():
                if metric in sensor_readings:
                    actual_value = sensor_readings[metric]
                    
                    # Check "less_than_or_equal_to"
                    if 'less_than_or_equal_to' in checks:
                        if actual_value <= checks['less_than_or_equal_to']:
                            rule_triggered = True
                    
                    # Check "less_than"
                    elif 'less_than' in checks and 'or_greater_than' not in checks:
                        if actual_value < checks['less_than']:
                            rule_triggered = True

                    # Check pH bands (complex logic: low OR high)
                    elif 'less_than' in checks and 'or_greater_than' in checks:
                        if actual_value < checks['less_than'] or actual_value > checks['or_greater_than']:
                            rule_triggered = True
                            
        # D. GENERATE RESPONSE IF RULE TRIGGERED
        if rule_triggered:
            template = rule['action_template']
            
            # Fetch target values dynamically based on stage
            # (Navigate the JSON: nutrient_targets -> growth_stages -> current_stage)
            stage_info = rules_data['nutrient_targets_by_growth_stage']['growth_stages'].get(current_growth_stage, {})
            targets = stage_info.get('recommended_annual_dose_kg_per_ha', {})

            # Fill the template
            response = template.format(
                crop=rules_data['metadata']['crop'], 
                growth_stage=current_growth_stage,
                live_N=sensor_readings.get('soil_nitrogen_ppm_or_kg_per_ha', 'N/A'),
                live_P=sensor_readings.get('available_P2O5_kg_per_ha', 'N/A'),
                live_K=sensor_readings.get('available_K2O_kg_per_ha', 'N/A'),
                live_pH=sensor_readings.get('soil_pH', 'N/A'), # Keep this one
                units="kg/ha", 
                target_N=targets.get('N', '?'), 
                target_P=targets.get('P2O5', '?'), 
                target_K=targets.get('K2O', '?'),
                target_units="kg/ha", 
                suggested_N_rate_kg_per_ha=100, 
                latest_lab_date="2024-10-01"
            )
            return response

    # Default if no rules are triggered
    return rules_data['response_templates_and_placeholders']['recommendation_style_guidelines']['example_no_response']


# --- 3. SIMULATION (Run this to test) ---
if __name__ == "__main__":
    rules = load_rules()
    print(f"Loaded rules for: {rules['metadata']['single_plot_id']}")

    # SCENARIO 1: Plot needs Nitrogen
    print("\n--- Scenario 1: Plot needs Nitrogen ---")
    stage_1 = "high_demand_plucking_flush"
    sensors_1 = {
        "soil_nitrogen_ppm_or_kg_per_ha": 200, # Alert trigger (Limit is 250)
        "available_P2O5_kg_per_ha": 50,
        "available_K2O_kg_per_ha": 200,
        "soil_pH": 5.0
    }
    print(evaluate_nutrient_needs(stage_1, sensors_1, rules))

    # SCENARIO 2: Plot is Healthy
    print("\n--- Scenario 2: Healthy Plot ---")
    stage_2 = "vegetative_maintenance"
    sensors_2 = {
        "soil_nitrogen_ppm_or_kg_per_ha": 300, # Healthy
        "available_P2O5_kg_per_ha": 50,
        "available_K2O_kg_per_ha": 200,
        "soil_pH": 5.0
    }
    print(evaluate_nutrient_needs(stage_2, sensors_2, rules))