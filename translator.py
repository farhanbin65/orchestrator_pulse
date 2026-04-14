import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def translate_to_bangla(text, is_headline=False):
    """
    Translates English news to Bangla.
    Updated to explicitly strip technical metadata (arXiv IDs, Abstract tags).
    """
    if is_headline:
        role_instruction = (
            "You are a professional Bangla news editor. Rewrite the headline to be "
            "catchy and concise. Remove any technical IDs or paper codes."
        )
    else:
        role_instruction = (
            "You are a professional Bangla news writer. Rewrite the summary to be "
            "detailed (4-5 sentences). IMPORTANT: Do not include words like 'Abstract', "
            "'arXiv', or 'Announce Type'. Focus only on the news content."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
               {"role": "system", "content": role_instruction},
               {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        return text