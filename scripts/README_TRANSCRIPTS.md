# Transcript Ingestion Script

This script ingests transcript PDFs into the Pinecone `transcripts` namespace.

## Setup

1. **Install dependencies:**
   ```bash
   pip install openai pinecone-client pypdf
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export PINECONE_API_KEY="your-pinecone-api-key"
   export PINECONE_INDEX_NAME="ipcs"  # optional, defaults to "ipcs"
   ```

3. **Create the transcripts folder:**
   ```bash
   mkdir -p data/transcripts
   ```

4. **Add your transcript PDFs:**
   - Place all transcript PDF files in `data/transcripts/`
   - The script will process all `.pdf` files in this folder

## Usage

```bash
python scripts/ingest_transcripts.py
```

Or make it executable and run directly:

```bash
chmod +x scripts/ingest_transcripts.py
./scripts/ingest_transcripts.py
```

## What it does

1. Reads all PDF files from `data/transcripts/`
2. Extracts text from each page
3. Splits text into chunks (~1500 characters with 200 char overlap)
4. Generates embeddings using OpenAI `text-embedding-3-large` (3072 dimensions)
5. Uploads to Pinecone index `ipcs` in namespace `transcripts`

## Configuration

You can adjust these variables in the script:

- `CHARS_PER_CHUNK = 1500` - Size of each text chunk
- `CHUNK_OVERLAP = 200` - Overlap between chunks
- `BATCH_SIZE = 50` - Number of vectors to upload per batch

## Output

Each chunk is stored with metadata:
- `source_name`: PDF filename
- `source_path`: Full path to PDF
- `chunk_index`: Index of chunk within the PDF
- `total_chunks`: Total number of chunks in the PDF
- `text`: The actual chunk text
- `chunk_type`: "text"
- `source_url`: File URL
- `source_description`: Description of the source

## Notes

- The script processes PDFs sequentially to avoid rate limits
- Each chunk gets a unique ID: `{pdf-name}-chunk-{index}-{uuid}`
- If a PDF has no extractable text, it will be skipped with a warning

