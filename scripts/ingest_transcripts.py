#!/usr/bin/env python3
"""
Script to ingest transcript PDFs into Pinecone 'transcripts' namespace.
Extracts company name, interviewee name, and transcript text.
Usage: python scripts/ingest_transcripts.py
"""

import os
import re
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from openai import OpenAI
from pinecone import Pinecone
from pypdf import PdfReader

# === Configuration ===
PDF_FOLDER = Path("data/transcripts")  # Put your transcript PDFs here
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "ipcs")
PINECONE_NAMESPACE = "transcripts"
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMENSION = 3072
BATCH_SIZE = 50  # Pinecone batch size

# === Clients ===
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pinecone_client = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pinecone_client.Index(PINECONE_INDEX)

# Lock for thread-safe Pinecone operations
pinecone_lock = Lock()


def extract_text_from_pdf(path: Path) -> str:
    """Extract raw text from PDF."""
    reader = PdfReader(str(path))
    pages = []
    
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    
    return "\n\n".join(pages)


def chunk_text_for_processing(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks that fit within token limits."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for paragraph break first
            para_break = text.rfind('\n\n', start, end)
            if para_break > start:
                end = para_break + 2
            else:
                # Look for sentence break
                sentence_break = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end)
                )
                if sentence_break > start:
                    end = sentence_break + 2
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    
    return chunks


def clean_text_chunk_with_openai(chunk: str) -> str:
    """Clean a single text chunk using OpenAI."""
    if not chunk or len(chunk.strip()) < 10:
        return chunk
    
    prompt = f"""Clean and normalize this interview transcript text chunk. Fix any spacing issues (e.g., "v i e w e r" should become "viewer"). Remove excessive whitespace. Preserve the conversation structure between Interviewer and Candidate.

Raw text chunk:
{chunk}

Return only the cleaned text, nothing else."""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You clean and normalize interview transcript text. Return only the cleaned text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=8000  # Allow longer responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      ⚠️  Chunk cleaning failed: {e}, using original")
        return chunk


def detect_interview_boundaries(raw_text: str) -> List[Tuple[int, int]]:
    """Detect multiple interviews in a PDF and return their boundaries."""
    # Use OpenAI to identify interview boundaries
    # Sample first 10000 chars to detect pattern
    sample_text = raw_text[:10000] if len(raw_text) > 10000 else raw_text
    
    prompt = f"""Analyze this PDF content and identify if it contains multiple separate interview transcripts. 

Look for patterns like:
- New sections starting with "Company:", "Interview with:", "Candidate:", "Round", etc.
- Clear separators between different interviews
- Different company names or interviewee names appearing

If there are multiple interviews, identify the approximate character positions where each interview starts and ends.

Return JSON with:
- "has_multiple_interviews": boolean
- "interviews": array of objects with "start_char" and "end_char" positions (if multiple)

If single interview, return:
{{"has_multiple_interviews": false, "interviews": [{{"start_char": 0, "end_char": {len(raw_text)}}}]}}

Sample text:
{sample_text[:8000]}
"""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You analyze PDF content to identify interview boundaries. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if result.get("has_multiple_interviews", False):
            interviews = result.get("interviews", [])
            boundaries = [(int(i["start_char"]), int(i["end_char"])) for i in interviews]
            return boundaries
        else:
            # Single interview - return full text range
            return [(0, len(raw_text))]
            
    except Exception as e:
        print(f"    ⚠️  Interview detection failed: {e}, treating as single interview")
        return [(0, len(raw_text))]


def split_interviews_from_text(raw_text: str) -> List[str]:
    """Split PDF text into individual interview transcripts."""
    boundaries = detect_interview_boundaries(raw_text)
    
    interviews = []
    for start, end in boundaries:
        interview_text = raw_text[start:end].strip()
        if len(interview_text) > 100:  # Minimum length check
            interviews.append(interview_text)
    
    return interviews if interviews else [raw_text]


def extract_company_and_interviewee_with_openai(text_chunk: str) -> Tuple[str, str]:
    """Extract company and interviewee from a transcript chunk."""
    prompt = f"""You are analyzing an interview transcript. Extract:

1. Company Name: The name of the company conducting the interview (e.g., "KPMG", "BITSvertise", "Aditya Birla Group", etc.). If not found, return "Unknown".

2. Interviewee Name: The full name of the person being interviewed (candidate). Look for patterns like "Candidate:", "Interviewee:", or names mentioned. If not found, return "Unknown".

Return your response as a JSON object with these exact keys:
- "company": string
- "interviewee": string

Transcript excerpt:
{text_chunk[:6000]}
"""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract structured information from interview transcripts. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("company", "Unknown"), result.get("interviewee", "Unknown")
    except Exception as e:
        print(f"      ⚠️  Company/interviewee extraction failed: {e}")
        return "Unknown", "Unknown"


def extract_structured_info_with_openai(raw_text: str) -> Dict[str, str]:
    """Use OpenAI to extract company name, interviewee name, and clean transcript."""
    if not raw_text or len(raw_text.strip()) < 50:
        return {
            "company": "Unknown",
            "interviewee": "Unknown",
            "transcript": raw_text or ""
        }
    
    # Extract company and interviewee from first chunk
    print(f"    📋 Extracting company and interviewee names...")
    first_chunk = raw_text[:6000]  # First 6000 chars should have company/interviewee info
    company, interviewee = extract_company_and_interviewee_with_openai(first_chunk)
    
    # Split transcript into chunks for cleaning
    print(f"    🧹 Cleaning transcript in chunks...")
    text_chunks = chunk_text_for_processing(raw_text, chunk_size=5000)
    print(f"    📦 Split into {len(text_chunks)} chunks for processing")
    
    # Clean each chunk in parallel
    cleaned_chunks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_chunk = {
            executor.submit(clean_text_chunk_with_openai, chunk): i 
            for i, chunk in enumerate(text_chunks)
        }
        
        results = [None] * len(text_chunks)
        for future in as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                cleaned = future.result()
                results[chunk_idx] = cleaned
            except Exception as e:
                print(f"      ⚠️  Error cleaning chunk {chunk_idx}: {e}")
                results[chunk_idx] = text_chunks[chunk_idx]  # Use original if cleaning fails
        
        cleaned_chunks = results
    
    # Combine cleaned chunks
    cleaned_transcript = "\n\n".join(cleaned_chunks)
    
    return {
        "company": company,
        "interviewee": interviewee,
        "transcript": cleaned_transcript
    }


def chunk_for_embedding(text: str, max_chars: int = 6000) -> List[str]:
    """Split text into chunks suitable for embedding (stays under token limits)."""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            # Try to break at paragraph boundary
            para_break = text.rfind('\n\n', start, end)
            if para_break > start:
                end = para_break + 2
            else:
                # Try sentence boundary
                sentence_break = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('\n', start, end)
                )
                if sentence_break > start:
                    end = sentence_break + 2
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    
    return chunks


def create_transcript_records(
    company: Optional[str],
    interviewee: Optional[str],
    transcript_text: str,
    source_filename: str,
    source_path: str
) -> List[Dict]:
    """Create multiple Pinecone records for a transcript, chunking if necessary."""
    # Chunk transcript for embedding (max 6000 chars per chunk to stay under token limit)
    transcript_chunks = chunk_for_embedding(transcript_text, max_chars=6000)
    
    records = []
    
    for i, chunk_text in enumerate(transcript_chunks):
        # Create searchable text with metadata
        searchable_text = f"Company: {company or 'Unknown'}\n"
        searchable_text += f"Interviewee: {interviewee or 'Unknown'}\n"
        searchable_text += f"Transcript excerpt:\n{chunk_text}"
        
        # Generate embedding
        try:
            embedding = openai_client.embeddings.create(
                model=EMBED_MODEL,
                input=searchable_text,
            ).data[0].embedding
        except Exception as e:
            print(f"      ⚠️  Embedding failed for chunk {i+1}: {e}")
            # Skip this chunk if embedding fails
            continue
        
        records.append({
            "id": f"transcript-{uuid.uuid4().hex}",
            "values": embedding,
            "metadata": {
                "company": company or "Unknown",
                "interviewee": interviewee or "Unknown",
                "transcript": chunk_text,
                "chunk_index": i,
                "total_chunks": len(transcript_chunks),
                "source_name": source_filename,
                "source_path": source_path,
                "source_url": f"file://{source_path}",
                "source_description": f"Interview transcript: {company or 'Unknown'} - {interviewee or 'Unknown'} (chunk {i+1}/{len(transcript_chunks)})",
                "chunk_type": "transcript",
            },
        })
    
    return records


def process_single_interview(
    interview_text: str,
    interview_num: int,
    total_interviews: int,
    source_filename: str,
    source_path: str
) -> List[Dict]:
    """Process a single interview transcript and return Pinecone records."""
    print(f"    📝 Processing interview {interview_num}/{total_interviews}...")
    
    # Extract company and interviewee from first chunk
    first_chunk = interview_text[:6000]
    company, interviewee = extract_company_and_interviewee_with_openai(first_chunk)
    
    # Clean the transcript
    print(f"      🧹 Cleaning transcript...")
    text_chunks = chunk_text_for_processing(interview_text, chunk_size=5000)
    
    cleaned_chunks = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_chunk = {
            executor.submit(clean_text_chunk_with_openai, chunk): i 
            for i, chunk in enumerate(text_chunks)
        }
        
        results = [None] * len(text_chunks)
        for future in as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                cleaned = future.result()
                results[chunk_idx] = cleaned
            except Exception as e:
                print(f"        ⚠️  Error cleaning chunk {chunk_idx}: {e}")
                results[chunk_idx] = text_chunks[chunk_idx]
        
        cleaned_chunks = results
    
    cleaned_transcript = "\n\n".join(cleaned_chunks)
    
    print(f"      Company: {company}, Interviewee: {interviewee}")
    print(f"      Cleaned length: {len(cleaned_transcript)} chars")
    
    # Create records
    records = create_transcript_records(
        company=company,
        interviewee=interviewee,
        transcript_text=cleaned_transcript,
        source_filename=source_filename,
        source_path=source_path
    )
    
    return records


def process_pdf(pdf_path: Path) -> int:
    """Process a single PDF and return number of records created."""
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*60}")
    
    # Extract raw text from PDF
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text or len(raw_text.strip()) < 100:
        print(f"  ⚠️  No meaningful text extracted from {pdf_path.name}")
        return 0
    
    print(f"  Extracted {len(raw_text)} characters")
    
    # Detect and split multiple interviews
    print(f"  🔍 Detecting interview boundaries...")
    interview_texts = split_interviews_from_text(raw_text)
    print(f"  Found {len(interview_texts)} interview(s) in this PDF")
    
    if not interview_texts:
        print(f"  ⚠️  No interviews detected")
        return 0
    
    # Process each interview
    all_records = []
    for i, interview_text in enumerate(interview_texts, 1):
        try:
            records = process_single_interview(
                interview_text=interview_text,
                interview_num=i,
                total_interviews=len(interview_texts),
                source_filename=pdf_path.name,
                source_path=str(pdf_path.resolve())
            )
            all_records.extend(records)
        except Exception as e:
            print(f"    ❌ Error processing interview {i}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_records:
        print(f"  ⚠️  No records created from this PDF")
        return 0
    
    # Upsert all records to Pinecone in batches (thread-safe)
    print(f"  📦 Uploading {len(all_records)} record(s) to Pinecone...")
    with pinecone_lock:
        for i in range(0, len(all_records), BATCH_SIZE):
            batch = all_records[i:i + BATCH_SIZE]
            index.upsert(vectors=batch, namespace=PINECONE_NAMESPACE)
    
    print(f"  ✅ Successfully ingested {len(all_records)} record(s) from {len(interview_texts)} interview(s)")
    
    return len(all_records)


def main():
    """Main function to process all PDFs in the transcripts folder."""
    print("=" * 60)
    print("Transcript PDF Ingestion Script (AI-Powered + Parallel)")
    print("=" * 60)
    print(f"PDF Folder: {PDF_FOLDER.resolve()}")
    print(f"Pinecone Index: {PINECONE_INDEX}")
    print(f"Namespace: {PINECONE_NAMESPACE}")
    print(f"Embedding Model: {EMBED_MODEL} ({EMBED_DIMENSION} dimensions)")
    print(f"Extraction: Using OpenAI GPT-4o-mini for structured extraction")
    print(f"Processing: Parallel execution enabled (up to 4 PDFs simultaneously)")
    print("=" * 60)
    
    # Check if PDF folder exists
    if not PDF_FOLDER.exists():
        print(f"\n❌ Error: PDF folder not found: {PDF_FOLDER.resolve()}")
        print(f"   Please create the folder and add your transcript PDFs there.")
        return
    
    # Find all PDF files
    pdf_paths = sorted(PDF_FOLDER.glob("*.pdf"))
    if not pdf_paths:
        print(f"\n❌ No PDF files found in {PDF_FOLDER.resolve()}")
        print(f"   Please add your transcript PDFs to this folder.")
        return
    
    print(f"\nFound {len(pdf_paths)} PDF file(s):")
    for pdf_path in pdf_paths:
        print(f"  - {pdf_path.name}")
    
    # Ask user for parallel processing preference
    print(f"\n💡 Processing with parallel execution (using ThreadPoolExecutor)")
    print(f"   Will process multiple PDFs simultaneously for faster ingestion")
    
    # Process PDFs in parallel
    total_records = 0
    start_time = time.time()
    max_workers = min(4, len(pdf_paths))  # Process up to 4 PDFs in parallel
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all PDFs for processing
        future_to_pdf = {
            executor.submit(process_pdf, pdf_path): pdf_path 
            for pdf_path in pdf_paths
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_pdf):
            pdf_path = future_to_pdf[future]
            try:
                count = future.result()
                total_records += count
            except Exception as e:
                print(f"\n  ❌ Error processing {pdf_path.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print(f"Total PDFs processed: {len(pdf_paths)}")
    print(f"Total records created: {total_records}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Namespace: {PINECONE_NAMESPACE}")
    print("=" * 60)
    print("\n⚠️  Note: If you had previous data in this namespace, delete it first!")
    print("   You can delete the namespace in Pinecone dashboard or use:")
    print("   index.delete(delete_all=True, namespace='transcripts')")


if __name__ == "__main__":
    # Check environment variables
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        exit(1)
    
    if not os.environ.get("PINECONE_API_KEY"):
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        exit(1)
    
    main()
