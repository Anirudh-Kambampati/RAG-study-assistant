from langchain_ollama import OllamaLLM


def get_llm():
    return OllamaLLM(
        model="phi3:mini",   # 👈 lightweight
        temperature=0.1,
        num_ctx=4096,        # limit context
        num_predict=800      # limit output tokens
    )
