
from pdf_processor import extract_text_from_pdf
from chunking import split_text
from embedding_service import generate_embeddings


def process_pdf(uploaded_file):

    # 1. Extract text from uploaded PDF
    extracted_text = extract_text_from_pdf(uploaded_file)

    # 2. Divide extracted text into chunks
    chunks = split_text(
        extracted_text,
        chunk_size=500,
        overlap=100
    )

    if not chunks:
        raise ValueError("No text chunks were generated.")

    # 3. Generate embeddings for all chunks
    embeddings = generate_embeddings(chunks)

    # 4. Return processed document information
    return {
        "filename": uploaded_file.name,
        "text": extracted_text,
        "chunks": chunks,
        "embeddings": embeddings
    }
