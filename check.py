from dotenv import load_dotenv
from google import genai

from config.settings import get_gemini_api_key

load_dotenv()

client = genai.Client(api_key=get_gemini_api_key())

print("Modelos disponíveis para generateContent:")
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(f"  {model.name}")
