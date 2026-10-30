
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

try:
    response = client.responses.create(
        model="gpt-5.4-nano",
        input="Reply with exactly: ResearchLens API connection successful.",
        max_output_tokens=200,
    )

    print("Status:", response.status)
    print("Response:", response.output_text)

    if response.usage:
        print("Input tokens:", response.usage.input_tokens)
        print("Output tokens:", response.usage.output_tokens)

except Exception as e:
    print("API error:", type(e).__name__)
    print(str(e))
