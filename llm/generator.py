import os
from langchain_openai import ChatOpenAI

def get_llm():
    backend = os.getenv("LLM_BACKEND", "hosted").lower()

    # -----------------------
    # PRIMARY: Groq
    # -----------------------
    if backend == "hosted":
        try:
            print("Using Groq (primary)")
            return ChatOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY"),
                model="openai/gpt-oss-120b",
                temperature=0.1,
            )
        except Exception as e:
            print(f"Groq failed: {e}")

            # fallback to OpenRouter
            return get_fallback_llm()

    # -----------------------
    # FALLBACK DIRECT
    # -----------------------
    elif backend == "fallback":
        return get_fallback_llm()

    else:
        raise ValueError("Invalid LLM_BACKEND")


# -----------------------
# FALLBACK LLM
# -----------------------
def get_fallback_llm():
    print("Using OpenRouter fallback (Gemma 4 26B A4B, free)")

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="google/gemma-4-26b-a4b-it:free",
        temperature=0.1,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Metis",
        },
    )