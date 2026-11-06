
from dotenv import load_dotenv

from src.generation.client import OpenAIClient
from src.generation.config import GenerationConfig

load_dotenv()

config = GenerationConfig.from_env()
client = OpenAIClient(config)

messages = [
    {
        "role": "system",
        "content": (
            "You are a scientific research assistant. "
            "Answer using only the provided evidence. "
            "Return structured JSON matching the required schema."
        ),
    },
    {
        "role": "user",
        "content": (
            "Question: What is SelfCheckGPT?\n\n"
            "Evidence [S1]: SelfCheckGPT is a method for "
            "detecting hallucinations in large language models "
            "by checking consistency across multiple generated responses."
        ),
    },
]

try:
    answer, metrics = client.complete(messages)

    print("=== GENERATED ANSWER ===")
    print(answer.model_dump_json(indent=2))

    print("\n=== METRICS ===")
    print(metrics.model_dump_json(indent=2))

except Exception as e:
    print("Error:", type(e).__name__)
    print(str(e))

finally:
    client.close()
