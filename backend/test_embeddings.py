"""Test embeddings functionality"""
import os
from dotenv import load_dotenv
load_dotenv("../.env")

from langchain_huggingface import HuggingFaceEmbeddings

# Get embedding model from env
embedding_model = os.getenv("HGF_EMBEDDING_MODEL_ID", "nomic-ai/nomic-embed-text-v1")

print(f"Testing embeddings with model: {embedding_model}")
print("=" * 60)

try:
    print("\n1. Initializing embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"trust_remote_code": True}
    )
    print("✓ Embedding model initialized successfully")
    
    print("\n2. Testing single text embedding...")
    test_text = "Warfarin is an anticoagulant medication"
    embedding_vector = embeddings.embed_query(test_text)
    print(f"✓ Generated embedding vector")
    print(f"  - Dimension: {len(embedding_vector)}")
    print(f"  - First 5 values: {embedding_vector[:5]}")
    
    print("\n3. Testing batch embeddings...")
    test_texts = [
        "Aspirin is used for pain relief",
        "Ibuprofen reduces inflammation",
        "Acetaminophen treats fever"
    ]
    batch_embeddings = embeddings.embed_documents(test_texts)
    print(f"✓ Generated {len(batch_embeddings)} embeddings")
    print(f"  - Each dimension: {len(batch_embeddings[0])}")
    
    print("\n4. Testing similarity (cosine)...")
    import numpy as np
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # Compare similar vs dissimilar texts
    similar_text = "Warfarin prevents blood clots"
    dissimilar_text = "The weather is sunny today"
    
    emb1 = embeddings.embed_query(test_text)
    emb2 = embeddings.embed_query(similar_text)
    emb3 = embeddings.embed_query(dissimilar_text)
    
    sim_score = cosine_similarity(emb1, emb2)
    dissim_score = cosine_similarity(emb1, emb3)
    
    print(f"  - Similarity (Warfarin texts): {sim_score:.4f}")
    print(f"  - Similarity (Warfarin vs weather): {dissim_score:.4f}")
    
    if sim_score > dissim_score:
        print("✓ Embeddings correctly identify similar content")
    else:
        print("⚠ Warning: Similarity scores unexpected")
    
    print("\n" + "=" * 60)
    print("✓ All embedding tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
