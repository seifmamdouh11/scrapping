import pandas as pd
import json

# Load the categories
with open('categories.json', 'r', encoding='utf-8') as f:
    categories = json.load(f)

# Create a mapping from ID to Name
id_to_name = {cat["_id"]["$oid"]: cat["name"] for cat in categories}

# Load the jobs CSV
try:
    df = pd.read_csv('creative_and_design_jobs.csv')
    
    # Replace the IDs with the actual names
    df['category'] = df['category'].map(id_to_name).fillna(df['category'])
    
    # Save it back
    df.to_csv('creative_and_design_jobs_final.csv', index=False, encoding='utf-8')
    print("Successfully converted category IDs to names! Saved as creative_and_design_jobs_final.csv")
except Exception as e:
    print(f"Error processing CSV: {e}")
