# Multi-Tool Agent Architecture

## Overview

MedicaLLM uses LangGraph's ReAct (Reasoning + Acting) pattern, which enables the agent to chain multiple tools together in a single query. This is similar to how advanced AI assistants like Kiro work.

## How It Works

### ReAct Loop

The agent follows this cycle until it has enough information to answer:

```
1. THOUGHT: "I need drug information first"
   ↓
2. ACTION: Call get_drug_info("aspirin")
   ↓
3. OBSERVATION: Receives drug data
   ↓
4. THOUGHT: "Now I should check for interactions"
   ↓
5. ACTION: Call check_drug_interaction("aspirin", "warfarin")
   ↓
6. OBSERVATION: Receives interaction data
   ↓
7. THOUGHT: "Let me find research evidence"
   ↓
8. ACTION: Call search_pubmed("aspirin warfarin interaction")
   ↓
9. OBSERVATION: Receives research articles
   ↓
10. THOUGHT: "I have enough information to answer"
    ↓
11. FINAL ANSWER: Comprehensive response with all gathered data
```

### Configuration

- **Max Iterations**: 50 reasoning steps (configurable in `agent.py`)
- **Max Tokens**: 4096 tokens for comprehensive responses
- **Temperature**: 0.3 for consistent, focused reasoning

### Example Multi-Tool Flows

#### Complex Drug Query
```
User: "Tell me about aspirin for heart disease and if it's safe with warfarin"

Agent reasoning:
1. get_drug_info("aspirin") → Get basic drug info
2. search_drugs_by_indication("cardiovascular disease") → Find related drugs
3. check_drug_interaction("aspirin", "warfarin") → Check safety
4. search_pubmed("aspirin warfarin bleeding risk") → Get evidence
5. recommend_alternative_drug("aspirin") → Suggest alternatives if needed
6. search_medical_documents("antiplatelet therapy guidelines") → Get clinical guidelines

Result: Comprehensive answer with drug info, interaction warnings, research evidence, and alternatives
```

#### Patient Safety Analysis
```
User: "Analyze my patient's medications"

Agent reasoning:
1. analyze_patient_medications(patient_id) → Run full safety check
2. For each interaction found:
   - search_pubmed(drug1 + drug2 + "interaction") → Get research
   - recommend_alternative_drug(problematic_drug) → Find alternatives
3. search_medical_documents("polypharmacy management") → Get guidelines

Result: Complete safety report with evidence-based recommendations
```

## System Prompt Design

The system prompt explicitly encourages multi-tool usage:

```
MULTI-TOOL REASONING:
You can and SHOULD use multiple tools in a single query when needed:
- Start with foundational tools (get_drug_info, check_drug_interaction)
- Then use specialized tools (search_medical_documents, search_pubmed)
- Chain tools logically: drug info → interactions → guidelines → research → alternatives
- Think step-by-step
```

## Streaming Support

The streaming endpoint (`/query-stream`) shows the agent's thinking process in real-time:

```json
{"type": "thinking", "step": "Looking up drug information...", "tool": "get_drug_info"}
{"type": "thinking", "step": "Checking drug-drug interactions...", "tool": "check_drug_interaction"}
{"type": "thinking", "step": "Searching PubMed literature...", "tool": "search_pubmed"}
{"type": "thinking", "step": "Generating response...", "tool": null}
{"type": "content", "content": "Based on my analysis..."}
```

## Best Practices

### For Tool Developers

1. **Keep tools focused**: Each tool should do one thing well
2. **Return structured data**: Make it easy for the agent to chain tools
3. **Include metadata**: Help the agent decide when to use the tool
4. **Handle errors gracefully**: Don't break the reasoning chain

### For Prompt Engineers

1. **Provide examples**: Show the agent how to chain tools
2. **Explain the "why"**: Help the agent understand when to use multiple tools
3. **Set expectations**: Tell the agent to be thorough, not just fast
4. **Guide the flow**: Suggest logical tool sequences

### For Users

The agent will automatically use multiple tools when needed. You don't need to ask for it explicitly:

- ❌ "First check the drug info, then check interactions, then search PubMed"
- ✅ "Tell me about aspirin for heart disease and if it's safe with warfarin"

## Comparison to Other Architectures

### Traditional Chatbots
- Single tool per query
- No reasoning between tools
- Limited context awareness

### MedicaLLM (ReAct Pattern)
- Multiple tools per query
- Reasoning between each tool call
- Builds context progressively
- Adapts based on findings

### Advanced AI Assistants (like Kiro)
- Similar ReAct pattern
- Extensive tool library
- Parallel tool execution (future enhancement)
- Self-correction and retry logic

## Future Enhancements

1. **Parallel Tool Execution**: Call independent tools simultaneously
2. **Tool Result Caching**: Avoid redundant calls within a session
3. **Adaptive Iteration Limits**: Increase limit for complex queries
4. **Tool Confidence Scores**: Help agent decide when to stop searching
5. **User Feedback Loop**: Learn which tool chains work best

## Monitoring

Track multi-tool usage in logs:

```python
pm.inf(f"Agent configured with max_iterations=50 for multi-tool reasoning")
pm.inf("Invoking agent...")  # Start of reasoning chain
pm.suc("Query processed successfully")  # End of chain
```

## Troubleshooting

### Agent stops after one tool
- Check system prompt includes multi-tool guidance
- Verify recursion_limit is set (default: 50)
- Ensure max_tokens is sufficient (4096+)

### Agent uses too many tools
- Reduce recursion_limit
- Add stopping criteria to system prompt
- Increase temperature for more decisive reasoning

### Agent doesn't chain tools logically
- Provide more examples in system prompt
- Improve tool descriptions
- Add explicit flow guidance

## References

- [LangGraph ReAct Agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#create_react_agent)
- [LangChain Streaming](https://python.langchain.com/docs/expression_language/streaming)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
