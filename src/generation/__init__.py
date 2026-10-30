"""Local generation; importing this package does not initialize retrieval."""
from .client import OpenAIClient
from .config import GenerationConfig
from .generator import ResearchGenerator
from .schemas import GenerationResponse

__all__ = ["ResearchGenerator", "GenerationConfig", "GenerationResponse", "OpenAIClient"]
