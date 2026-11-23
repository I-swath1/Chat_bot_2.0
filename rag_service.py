
from embedding_service import get_embedding
from retrieval import retrieve_relevant_chunks
from ollama_service import generate_response


def answer_from_document(question, chunks, chunk_embeddings):

    # 1. Convert the user's question into an embedding
    query_embedding = get_embedding(question)

    # 2. Retrieve the most relevant document chunks
    relevant_chunks = retrieve_relevant_chunks(
        query_embedding,
        chunks,
        chunk_embeddings,
        top_k=3
    )

    if not relevant_chunks:
        return "No relevant information was found in the document."

    # 3. Combine retrieved chunks into context
    context = "\n\n".join(
        item["text"] for item in relevant_chunks
    )

    # 4. Create a prompt for the LLM
    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using only the context below.

If the answer is not available in the context,
clearly say that the document does not contain the answer.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    # 5. Generate the final answer using Qwen
    answer = generate_response(prompt)

    return answer
