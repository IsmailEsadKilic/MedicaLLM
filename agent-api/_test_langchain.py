from langchain_ollama import OllamaLLM

# 1) Lokal model adı (ör: llama3, mistral, codellama, gemma vb.)
llm = OllamaLLM(model="gemma3")

# 2) Basit çağrı
prompt = ""

response = llm.invoke(prompt)

print(response)