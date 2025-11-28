#!/usr/bin/env python3
"""
Update specific placement records in Pinecone 'placements' namespace.

This script fetches records from Pinecone, updates metadata fields, and upserts them back.

Usage:
    1. Edit the UPDATES list below with the records you want to update
    2. python scripts/update_placements.py
"""

import os
import re
from datetime import datetime, timezone, timedelta
from typing import Dict

from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_INDEX = "ipcs"
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "placements")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not set")
``
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
index = pinecone_client.Index(PINECONE_INDEX)

# ============================================================================
# EDIT THIS SECTION: Add your updates here
# ============================================================================
# Format: {application_id: {metadata_field: new_value, ...}}
# Note: For dates, use epoch milliseconds (timestamp * 1000)

def date_to_epoch_ms(date_str: str, tz_offset_hours: int = 5, tz_offset_minutes: int = 30) -> int:
    """
    Convert date string to epoch milliseconds.
    Format: "28-Nov-25 20:00:00" (DD-Mon-YY HH:MM:SS)
    Default timezone: IST (UTC+5:30)
    """
    try:
        # Parse the date string
        dt = datetime.strptime(date_str, "%d-%b-%y %H:%M:%S")
        # Create timezone offset (IST = UTC+5:30)
        tz_offset = timezone(timedelta(hours=tz_offset_hours, minutes=tz_offset_minutes))
        dt = dt.replace(tzinfo=tz_offset)
        # Convert to UTC and then to epoch milliseconds
        dt_utc = dt.astimezone(timezone.utc)
        return int(dt_utc.timestamp() * 1000)
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected: DD-Mon-YY HH:MM:SS. Error: {e}")

# Update for company_id 468 (Gemini Solutions, application_id 557)
# Deadline: 28-Nov-25 20:00:00 IST
UPDATES: Dict[int, Dict[str, any]] = {
    557: {  # application_id
        "application_deadline": date_to_epoch_ms("28-Nov-25 20:00:00"),
    },
    # Add more updates here...
    # Example:
    # 558: {
    #     "application_deadline": date_to_epoch_ms("30-Nov-25 18:00:00"),
    # },
}

# ============================================================================


def main():
    if not UPDATES:
        print("No updates specified. Please edit the UPDATES dictionary in the script.")
        return
    
    vectors = []
    not_found = []
    
    for application_id, field_updates in UPDATES.items():
        vector_id = f"placement-{application_id}"
        
        # Fetch existing vector from Pinecone
        try:
            fetch_result = index.fetch(ids=[vector_id], namespace=PINECONE_NAMESPACE)
            if vector_id not in fetch_result.vectors:
                not_found.append(application_id)
                print(f"⚠️  Vector ID '{vector_id}' not found in Pinecone")
                continue
            
            existing_vector = fetch_result.vectors[vector_id]
            existing_metadata = existing_vector.metadata or {}
            
            print(f"\nUpdating application_id {application_id} (vector_id: {vector_id}):")
            
            # Update metadata fields
            updated_metadata = existing_metadata.copy()
            for field, new_value in field_updates.items():
                old_value = existing_metadata.get(field, "N/A")
                updated_metadata[field] = new_value
                
                # Show human-readable date conversion for deadlines
                if field == "application_deadline":
                    old_date_str = datetime.fromtimestamp(old_value / 1000).strftime('%Y-%m-%d %H:%M:%S') if isinstance(old_value, (int, float)) else str(old_value)
                    new_date_str = datetime.fromtimestamp(new_value / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {field}: {old_value} ({old_date_str}) → {new_value} ({new_date_str})")
                else:
                    print(f"  {field}: {old_value} → {new_value}")
                
                # If updating application_deadline, also update the text field
                if field == "application_deadline":
                    # Update the deadline date in the text field
                    old_text = existing_metadata.get("text", "")
                    if old_text:
                        # Extract old deadline date from text (format: "Deadline: YYYY-MM-DD")
                        old_deadline_match = re.search(r'Deadline: (\d{4}-\d{2}-\d{2})', old_text)
                        if old_deadline_match:
                            # Convert new epoch_ms to date string
                            new_date = datetime.fromtimestamp(new_value / 1000).date()
                            new_date_str = new_date.strftime("%Y-%m-%d")
                            # Replace in text
                            updated_text = re.sub(
                                r'Deadline: \d{4}-\d{2}-\d{2}',
                                f'Deadline: {new_date_str}',
                                old_text
                            )
                            updated_metadata["text"] = updated_text
                            print(f"  text (deadline line): Updated to 'Deadline: {new_date_str}'")
            
            # If 'order' field exists in metadata, update it to match application_id
            if 'order' in updated_metadata:
                updated_metadata['order'] = application_id
            
            # Prepare vector for upsert (keep existing values, update metadata)
            vectors.append({
                "id": vector_id,
                "values": existing_vector.values,  # Keep existing embedding
                "metadata": updated_metadata,
            })
            
        except Exception as e:
            print(f"⚠️  Error fetching vector '{vector_id}': {e}")
            not_found.append(application_id)
            continue
    
    if not_found:
        print(f"\n⚠️  Warning: {len(not_found)} vectors not found: {not_found}")
    
    if vectors:
        print(f"\n✓ Prepared {len(vectors)} updated records")
        print(f"Upserting to '{PINECONE_NAMESPACE}' namespace...")
        index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE)
        print(f"✓ Successfully updated {len(vectors)} placement records in Pinecone!")
    else:
        print("No vectors to upsert.")


if __name__ == "__main__":
    main()
