import json
import os

filename = 'technology_and_it_jobs.json'

if not os.path.exists(filename):
    print(f"File {filename} not found.")
    exit(1)

with open(filename, 'r', encoding='utf-8') as f:
    jobs = json.load(f)

for job in jobs:
    # Fix casing for type and status to match template
    if job.get("type"):
        job["type"] = job["type"].lower()
    else:
        job["type"] = "full-time"
        
    job["status"] = "active"
    
    # Remove Wuzzuf footer from description if it exists
    desc = job.get("description", "")
    if "Links\n\nBlog" in desc:
        job["description"] = desc.split("Links\n\nBlog")[0].strip()

# Save back to the exact same file
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(jobs, f, indent=4, ensure_ascii=False)

print(f"Successfully updated {len(jobs)} jobs in {filename}!")
