import os
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM  # optional, can remove

def get_llm():
    backend = os.getenv("LLM_BACKEND", "hosted").lower()

    # -----------------------
    # PRIMARY: Groq
    # -----------------------
    if backend == "hosted":
        try:
            print("🌐 Using Groq (primary)")
            return ChatOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY"),
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=900,
            )
        except Exception as e:
            print(f"⚠️ Groq failed: {e}")

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
    print("🪂 Using OpenRouter fallback (Nemotron free)")

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="nvidia/nemotron-3-super-120b-v1:free",
        temperature=0.1,
        max_tokens=900,
    )