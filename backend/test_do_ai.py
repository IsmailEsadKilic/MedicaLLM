"""Test Digital Ocean AI connection"""
import os
from openai import OpenAI

# Load from .env
from dotenv import load_dotenv
load_dotenv("../.env")

api_key = os.getenv("MODEL_ACCESS_KEY")
model = os.getenv("DO_AI_MODEL", "openai-gpt-oss-120b")

print(f"Testing Digital Ocean AI...")
print(f"Model: {model}")
print(f"API Key: {api_key[:20]}..." if api_key else "API Key: None")

client = OpenAI(
    api_key=api_key,
    base_url="https://inference.do-ai.run/v1"
)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "Say hello in 5 words"}
        ],
        max_tokens=512,
        temperature=0.7
    )
    
    print(f"\nSuccess! Full response:")
    message = response.choices[0].message
    
    print(f"\nContent: {message.content}")
    print(f"\nReasoning content: {message.reasoning_content}")
    print(f"\nFinish reason: {response.choices[0].finish_reason}")
    
    # Try to extract actual response
    if message.content:
        print(f"\n✓ Got content: {message.content}")
    elif message.reasoning_content:
        print(f"\n⚠ Only reasoning content available")
        print(f"Reasoning: {message.reasoning_content[:200]}...")
    
except Exception as e:
    print(f"\nError: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
