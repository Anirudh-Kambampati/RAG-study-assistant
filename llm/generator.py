import os

from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI


def get_llm():
    """
    LLM_BACKEND=local   -> Ollama (phi3:mini)
    LLM_BACKEND=hosted  -> Groq API (LLaMA 3)
    """

    backend = os.getenv("LLM_BACKEND", "local").lower()

    if backend == "local":
        print("🧠 Using LOCAL Ollama model (phi3:mini)")
        return OllamaLLM(
            model="phi3:mini",
            temperature=0.1,
            num_ctx=2048,
            num_predict=600,
        )

    elif backend == "hosted":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        print("🌐 Using HOSTED Groq API (LLaMA 3.1-8B)")
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=900

        )

    else:
        raise ValueError("Invalid LLM_BACKEND (use local or hosted)")
