import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Retrieve available models
models = client.models.list()

# Display model names
for model in sorted(models.data, key=lambda m: m.id):
    print(model.id)