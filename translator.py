import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def translate_to_bangla(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
               {
                "role": "system",
                "content": "You are a professional Bangla news writer. Rewrite the given English news into natural, fluent Bangla. Do not translate word-for-word. Adapt phrases so they sound natural to Bangla readers. Use simple, clear, and commonly used Bangla words. Avoid awkward literal translations. Keep the meaning accurate but improve readability and flow. Write in a news style tone."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        return text  # fallback to original if translation fails