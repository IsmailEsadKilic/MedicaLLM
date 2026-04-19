#!/usr/bin/env python3
"""
Test script for verifying streaming implementation.

Usage:
    python test_streaming.py

This script tests the streaming endpoint without requiring authentication.
For production testing, use curl with a valid JWT token.
"""

import asyncio
import json
import sys
from typing import AsyncGenerator

try:
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install langchain-openai langgraph")
    sys.exit(1)


async def test_basic_streaming():
    """Test basic LLM streaming without agent."""
    print("=" * 60)
    print("Test 1: Basic LLM Streaming")
    print("=" * 60)
    
    # Note: Replace with your actual API key and model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        api_key="your-api-key-here",
        streaming=True,
        temperature=0.3,
    )
    
    print("\nStreaming response for: 'Count to 5'")
    print("-" * 60)
    
    try:
        async for chunk in model.astream("Count to 5"):
            if chunk.content:
                print(chunk.content, end="", flush=True)
        print("\n" + "-" * 60)
        print("✅ Basic streaming works!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


async def test_agent_streaming():
    """Test agent streaming with astream_events."""
    print("\n" + "=" * 60)
    print("Test 2: Agent Streaming with astream_events")
    print("=" * 60)
    
    # Create a simple agent
    model = ChatOpenAI(
        model="gpt-4o-mini",
        api_key="your-api-key-here",
        streaming=True,
        temperature=0.3,
    )
    
    agent = create_react_agent(model, tools=[])
    
    print("\nStreaming response for: 'What is 2+2?'")
    print("-" * 60)
    
    try:
        token_count = 0
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": "What is 2+2?"}]},
            version="v2",
        ):
            event_type = event.get("event")
            
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)
                    token_count += 1
        
        print("\n" + "-" * 60)
        print(f"✅ Agent streaming works! Received {token_count} tokens")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


async def test_sse_format():
    """Test SSE message formatting."""
    print("\n" + "=" * 60)
    print("Test 3: SSE Message Format")
    print("=" * 60)
    
    async def mock_stream() -> AsyncGenerator[dict, None]:
        """Mock streaming generator."""
        yield {"type": "thinking", "step": "Processing...", "tool": None}
        yield {"type": "content", "content": "Hello"}
        yield {"type": "content", "content": " world"}
        yield {"type": "done", "sources": [], "tool_used": None}
    
    print("\nSSE formatted output:")
    print("-" * 60)
    
    try:
        async for chunk in mock_stream():
            sse_message = f"data: {json.dumps(chunk)}\n\n"
            print(sse_message, end="")
        
        print("-" * 60)
        print("✅ SSE formatting works!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("\n🧪 MedicaLLM Streaming Tests\n")
    
    results = []
    
    # Test 1: Basic streaming
    # Note: Requires valid API key
    # results.append(await test_basic_streaming())
    
    # Test 2: Agent streaming
    # Note: Requires valid API key
    # results.append(await test_agent_streaming())
    
    # Test 3: SSE format (no API key needed)
    results.append(await test_sse_format())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
