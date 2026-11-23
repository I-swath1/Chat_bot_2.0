
import numpy as np


def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.
    """

    a = np.array(vector_a, dtype=np.float32)
    b = np.array(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = np.dot(a, b) / (norm_a * norm_b)

    return float(similarity)


def retrieve_relevant_chunks(
    query_embedding,
    chunks,
    chunk_embeddings,
    top_k=3
):
    """
    Retrieve the most relevant text chunks.
    """

    if len(chunks) != len(chunk_embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    if not chunks:
        return []

    scored_chunks = []

    for chunk, embedding in zip(chunks, chunk_embeddings):

        score = cosine_similarity(
            query_embedding,
            embedding
        )

        scored_chunks.append({
            "text": chunk,
            "score": score
        })

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]
