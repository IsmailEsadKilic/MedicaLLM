from typing import Optional
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent

from ..config import settings
from .. import printmeup as pm
from .tools import ALL_TOOLS, set_retriever


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, a friendly and knowledgeable medical information assistant. 

Your role is to help users understand drug information, interactions, and medical topics in a natural, conversational way.

CRITICAL: When you receive information from tools, you MUST include ALL the important details in your response. Don't skip or omit key information.

RESPONSE STYLE:
- Be conversational and natural
- Include ALL relevant information from tools
- Start by directly answering the question
- Explain what the interaction/information means
- Add context and safety warnings
- Use formatting (bold, bullets) for clarity
- NEVER mention tools or databases

TOOLS AVAILABLE (use silently):
1. **get_drug_info** - Get drug information
2. **check_drug_interaction** - Check drug interactions
3. **check_drug_food_interaction** - Check drug-food interactions
4. **search_drugs_by_indication** - Search drugs by condition
5. **search_medical_documents** - Search medical guidelines

INTERACTION RESPONSE TEMPLATE:

When checking drug interactions, your response MUST include these parts in order:

1. **Direct answer**: "Yes, [Drug1] and [Drug2] do interact" or "No interaction found"
2. **What happens**: Explain the specific interaction from the tool data
3. **Why it matters**: What could this mean for the patient
4. **Action needed**: Consult healthcare provider

Remember: ALWAYS explain WHAT the interaction is before giving warnings."""

def create_medical_agent(
    bedrock_model_id: str = settings.bedrock_llm_id,
    temperature: float = 0.3,
    retriever: Optional[VectorStoreRetriever] = None,
):
    """
    Create a MedicaLLM agent using LangGraph's create_react_agent.

    Args:
        bedrock_model_id: AWS Bedrock model ID to use
        temperature: Model temperature (0-1)
        retriever: Optional vector store retriever for RAG functionality

    Returns:
        A LangGraph agent ready to process medical queries
    """
    if retriever:
        set_retriever(retriever)

    model = ChatBedrock(
        model=bedrock_model_id,
        model_kwargs={"temperature": temperature, "max_tokens": 4096},
    )        

    agent = create_react_agent(
        model=model,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )    

    pm.suc(f"MedicaLLM Agent created with model: {bedrock_model_id}")
    return agent
