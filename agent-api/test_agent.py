"""
Quick Agent Test
================
Test the new MedicaLLM agent using create_medical_agent
"""

from medical_agent import create_medical_agent
import printmeup as pm
import asyncio

async def main():
    pm.inf("\n" + "="*60)
    pm.inf("🏥 MedicaLLM Agent Test")
    pm.inf("="*60 + "\n")
    
    # Initialize agent
    pm.inf("Initializing agent...")
    agent = create_medical_agent(
        ollama_model_name="llama2:latest",
        ollama_base_url="http://localhost:11434",
        temperature=0.3,
        retriever=None  # No RAG for this test
    )
    
    # Test 1: Drug Info
    pm.inf("\n📋 Test 1: Get Drug Information")
    pm.inf("-" * 60)
    result = agent.invoke({
        "messages": [{"role": "user", "content": "What is Warfarin used for?"}]
    })
    
    if result.get("messages"):
        pm.suc("Query successful!")
        answer = result["messages"][-1].content
        print(f"\n{answer[:300]}..." if len(answer) > 300 else f"\n{answer}")
    else:
        pm.err(m="Query failed: No response")
    
    # Test 2: Interaction Check
    pm.inf("\n📋 Test 2: Check Drug Interaction")
    pm.inf("-" * 60)
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Does Warfarin interact with Aspirin?"}]
    })
    
    if result.get("messages"):
        pm.suc("Query successful!")
        answer = result["messages"][-1].content
        print(f"\n{answer[:300]}..." if len(answer) > 300 else f"\n{answer}")
    else:
        pm.err(m="Query failed: No response")
    
    # Test 3: Synonym
    pm.inf("\n📋 Test 3: Drug Synonym Resolution")
    pm.inf("-" * 60)
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Tell me about Coumadin"}]
    })
    
    if result.get("messages"):
        pm.suc("Query successful!")
        answer = result["messages"][-1].content
        print(f"\n{answer[:300]}..." if len(answer) > 300 else f"\n{answer}")
    else:
        pm.err(m="Query failed: No response")
    
    pm.inf("\n" + "="*60)
    pm.suc("✅ Tests complete!")
    pm.inf("="*60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pm.inf("\n\nInterrupted by user")
    except Exception as e:
        pm.err(e=e, m="Test failed")
