import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


def main():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set."
        )

    client = genai.Client(
        api_key=api_key
    )

    print("Testing Gemini 3.6 Flash...")

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input="Reply with exactly: Gemini connection works."
    )

    print()
    print("Response:")
    print(interaction.output_text)


if __name__ == "__main__":
    main()