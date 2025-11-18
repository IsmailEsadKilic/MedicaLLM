from langchain_ollama import OllamaLLM
OLLAMA_URL = "http://10.91.136.163:11434"


# 1) Lokal model adı (ör: llama3, mistral, codellama, gemma vb.)
llm = OllamaLLM(model="gemma3", base_url=OLLAMA_URL)

# 2) Basit çağrı
prompt = "what is a llm?"

response = llm.invoke(prompt)

print(response)