from langchain_ollama import OllamaLLM
from main import MODEL_NAME, OLLAMA_URL

def main():
    # Create LLM instance
    llm = OllamaLLM(model=MODEL_NAME, base_url=OLLAMA_URL)
    
    # Invoke with a simple prompt
    prompt = "What is artificial intelligence?"
    print(f"Prompt: {prompt}\n")
    
    response = llm.invoke(prompt)
    print(f"Response: {response}")

if __name__ == "__main__":
    main()
