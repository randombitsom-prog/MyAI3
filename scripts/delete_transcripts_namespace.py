#!/usr/bin/env python3
"""
Script to delete all records from the 'transcripts' namespace in Pinecone.
Usage: python scripts/delete_transcripts_namespace.py
"""

import os
from pinecone import Pinecone

PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "ipcs")
PINECONE_NAMESPACE = "transcripts"

if __name__ == "__main__":
    if not os.environ.get("PINECONE_API_KEY"):
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        exit(1)
    
    print("=" * 60)
    print("Delete Transcripts Namespace")
    print("=" * 60)
    print(f"Index: {PINECONE_INDEX}")
    print(f"Namespace: {PINECONE_NAMESPACE}")
    print("=" * 60)
    
    confirm = input("\n⚠️  This will delete ALL records in the 'transcripts' namespace. Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        exit(0)
    
    try:
        pinecone_client = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index = pinecone_client.Index(PINECONE_INDEX)
        
        # Delete all vectors in the namespace
        index.delete(delete_all=True, namespace=PINECONE_NAMESPACE)
        
        print(f"\n✅ Successfully deleted all records from namespace '{PINECONE_NAMESPACE}'")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

