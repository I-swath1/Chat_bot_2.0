
import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text:latest"


def get_embedding(text):
    """
    Convert a text string into a numerical embedding vector.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        embedding = result.get("embedding")

        if not embedding:
            raise ValueError("No embedding returned by Ollama.")

        return embedding

    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to Ollama.")

    except requests.exceptions.Timeout:
        raise RuntimeError("Embedding generation timed out.")

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Ollama API error: {error}")


def generate_embeddings(texts):
    """
    Generate embeddings for multiple text chunks.
    """

    embeddings = []

    for text in texts:
        vector = get_embedding(text)
        embeddings.append(vector)

    return embeddings
