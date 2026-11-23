
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
You are a helpful and friendly AI assistant.

Your responsibilities:
1. Answer questions clearly and accurately.
2. Explain technical concepts in simple language.
3. Help with Python, SQL, programming and debugging.
4. Use previous conversation context to understand follow-up questions.
5. Give examples whenever requested.
6. Avoid unnecessarily repeating previous explanations.
7. If you do not know something, acknowledge it.

Keep explanations organized and easy to understand.
"""


def generate_response(user_message, conversation_history=None):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Add previous conversation
    if conversation_history:

        for message in conversation_history:

            messages.append({
                "role": message["role"],
                "content": message["content"]
            })

    # Add latest user question
    messages.append({
        "role": "user",
        "content": user_message
    })

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": 512
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        result = response.json()

        return result["message"]["content"].strip()

    except requests.exceptions.ConnectionError:

        return "Cannot connect to Ollama. Please check whether Ollama is running."

    except requests.exceptions.Timeout:

        return "The model took too long to respond. Please try again."

    except requests.exceptions.RequestException as error:

        return f"API Error: {error}"

    except (ValueError, KeyError, TypeError):

        return "Invalid response received from Ollama."
