#!/usr/bin/env python3
"""
Alternative approach: Use LinkedIn public profiles and manual data collection.
This approach is more ethical and doesn't violate LinkedIn's ToS.

Option 1: Manual collection via LinkedIn search
Option 2: Use LinkedIn Sales Navigator (paid, has API)
Option 3: Use third-party services like Apollo.io, ZoomInfo (paid APIs)
"""

import json
import csv
from typing import List, Dict
from datetime import datetime
import os


def create_manual_template():
    """Create a template for manual data entry."""
    template = {
        "instructions": [
            "1. Go to LinkedIn and search: 'BITSoM MBA'",
            "2. For each alumni profile you find:",
            "   - Copy their name",
            "   - Copy their profile URL",
            "   - Copy all companies from their Experience section",
            "3. Add entries to the 'alumni' array below",
            "4. Run this script to generate the companies list"
        ],
        "alumni": [
            {
                "name": "Example Name",
                "profile_url": "https://www.linkedin.com/in/example",
                "companies": ["Company 1", "Company 2", "Company 3"]
            }
        ]
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/linkedin_alumni_manual.json", "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    
    print("✅ Template created at data/linkedin_alumni_manual.json")
    print("   Edit this file with alumni data, then run:")
    print("   python scripts/process_manual_linkedin_data.py")


def process_manual_data(input_file: str = "data/linkedin_alumni_manual.json"):
    """Process manually collected LinkedIn data."""
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        print("   Run create_manual_template() first")
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    alumni = data.get("alumni", [])
    all_companies = set()
    
    for person in alumni:
        companies = person.get("companies", [])
        all_companies.update(companies)
    
    # Save results
    output = {
        "processed_at": datetime.now().isoformat(),
        "total_alumni": len(alumni),
        "total_companies": len(all_companies),
        "companies": sorted(list(all_companies)),
        "alumni": alumni
    }
    
    # Save JSON
    with open("data/bitcom_linkedin_alumni.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    os.makedirs("data", exist_ok=True)
    with open("data/bitcom_companies.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Company Name"])
        for company in sorted(all_companies):
            writer.writerow([company])
    
    print(f"✅ Processed {len(alumni)} alumni profiles")
    print(f"✅ Found {len(all_companies)} unique companies")
    print(f"💾 Results saved to:")
    print(f"   - data/bitcom_linkedin_alumni.json")
    print(f"   - data/bitcom_companies.csv")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create-template":
        create_manual_template()
    else:
        process_manual_data()

