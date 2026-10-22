
import os
from dotenv import load_dotenv
from groq import Groq

# Load API key from .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY is missing.")
    print("Check that your .env file is in the project root.")
    raise SystemExit(1)

print("API key loaded successfully.")

try:
    client = Groq(
        api_key=api_key,
        timeout=30
    )

    print("Sending request to Groq...")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Say hello in one short sentence."
            }
        ],
        max_tokens=300
    )

    message = response.choices[0].message
    usage = response.usage

    print("\n===== GROQ API TEST =====")
    print("Model:", response.model)
    print("Finish reason:", response.choices[0].finish_reason)
    print("Answer:", repr(message.content))

    if usage and usage.completion_tokens_details:
        print(
            "Reasoning tokens:",
            usage.completion_tokens_details.reasoning_tokens
        )

    print("Total tokens:", usage.total_tokens)

    if message.content and message.content.strip():
        print("\nSUCCESS: Groq returned a visible answer.")
    else:
        print(
            "\nWARNING: The response has no visible answer. "
            "Check the finish reason and token usage above."
        )

except Exception as error:
    print("\n===== GROQ API ERROR =====")
    print("Error type:", type(error).__name__)
    print("Error details:", str(error))
