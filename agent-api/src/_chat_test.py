"""
Conversational Test - Maintains History!
"""
import os
from vector_store import VectorStoreManager
from rag_chain import RAGChain

from main import MODEL_NAME, OLLAMA_URL

print("\n💬 Conversational PDF Q&A Test\n" + "="*60 + "\n")

# Database check
if not os.path.exists("../chroma_db"):
    print("❌ Database not found! First run: python main.py\n")
    exit(1)


# Setup
print("📂 Loading database...")
vs_manager = VectorStoreManager(ollama_model_name=MODEL_NAME)
vectorstore = vs_manager.load_vectorstore()

if not vectorstore:
    print("❌ Failed to load database!")
    exit(1)

print("✓ Database loaded\n")

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20}
)

print("🔗 Creating RAG Chain (QA mode)...")
rag = RAGChain(retriever, ollama_model_name=MODEL_NAME, ollama_base_url=OLLAMA_URL)
print("✓ Ready!\n")

print("="*60)
print("INTERACTIVE CHAT (QA Mode + Sources)")
print("="*60)
print("To exit: 'q' or 'quit'\n")

# Custom chat loop - Shows sources
while True:
    question = input("You: ").strip()
    
    if question.lower() in ['quit', 'exit', 'q']:
        print("See you later!")
        break
    
    if not question:
        continue
    
    try:
        response = rag.query(question, chain_type="qa")
        
        print(f"\n AI: {response['answer']}")
        
        # SHOW SOURCES
        if response.get('source_documents'):
            print(f"\n SOURCE DOCUMENTS:")
            print("-"*60)
            for i, doc in enumerate(response['source_documents'], 1):
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', '?')
                print(f"  [{i}] {source} (Page: {page})")
                print(f"      Content: {doc.page_content[:150]}...")
            print("-"*60)
        
        print()
        
    except Exception as e:
        print(f"Error: {e}\n")

print("\n Chat ended!\n")
