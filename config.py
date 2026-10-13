import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

WEBZ_URL = os.getenv('WEBZ_URL')

WEBZ_API_URL = "https://api.webz.io/api/news"

WEBZ_API_TOKEN = os.getenv("WEBZ_API_TOKEN")

SERP_API_KEY = os.getenv("SERP_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv("GROQ_MODEL")

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")