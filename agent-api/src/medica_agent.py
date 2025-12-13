"""
MedicaLLM Agent - Real LangChain Agent with Tool Calling
LLM decides which tool to use based on the question
"""

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field
import boto3
from botocore.config import Config
import json

# ============================================================
# DynamoDB Connection
# ============================================================

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy',
    config=Config(connect_timeout=5, read_timeout=5)
)

drugs_table = dynamodb.Table('Drugs')
interactions_table = dynamodb.Table('DrugInteractions')

# ============================================================
# RAG Chain Reference
# ============================================================

_rag_chain = None

def set_rag_chain(chain):
    """Set the RAG chain from the main application."""
    global _rag_chain
    _rag_chain = chain

def get_rag_chain():
    return _rag_chain

# ============================================================
# TOOLS - LLM will choose from these
# ============================================================

@tool
def get_drug_info(drug_name: Annotated[str, "Name of the drug to look up, e.g., Warfarin, Metformin, Aspirin"]) -> str:
    """
    Get detailed information about a specific drug from the database.
    Use this tool when the user asks about:
    - What a drug is or does
    - Drug indications (what it's used for)
    - Drug mechanism of action (how it works)
    - Drug side effects or toxicity
    - Drug metabolism, half-life, or pharmacokinetics
    
    Examples of questions that need this tool:
    - "What is Warfarin?"
    - "Tell me about Metformin"
    - "What are the side effects of Aspirin?"
    - "How does Lisinopril work?"
    """
    try:
        drug_name = drug_name.strip()
        
        # Try different cases
        for name_variant in [drug_name, drug_name.title(), drug_name.upper(), drug_name.lower()]:
            # First try direct lookup with META
            response = drugs_table.get_item(
                Key={'PK': f'DRUG#{name_variant}', 'SK': 'META'}
            )
            
            if 'Item' in response:
                drug = response['Item']
                break
            
            # Try synonym lookup
            synonym_response = drugs_table.get_item(
                Key={'PK': f'DRUG#{name_variant}', 'SK': 'SYNONYM'}
            )
            
            if 'Item' in synonym_response and 'points_to' in synonym_response['Item']:
                actual_name = synonym_response['Item']['points_to']
                response = drugs_table.get_item(
                    Key={'PK': f'DRUG#{actual_name}', 'SK': 'META'}
                )
                if 'Item' in response:
                    drug = response['Item']
                    break
        else:
            return f"Drug '{drug_name}' not found in database. Please check the spelling or try another drug name."
        
        # Format the response
        result = []
        result.append(f"📋 **{drug.get('name', drug_name)}**\n")
        
        if drug.get('description'):
            desc = str(drug['description'])[:600]
            if len(str(drug.get('description', ''))) > 600:
                desc += "..."
            result.append(f"**Description:** {desc}\n")
        
        if drug.get('indication'):
            ind = str(drug['indication'])[:500]
            if len(str(drug.get('indication', ''))) > 500:
                ind += "..."
            result.append(f"**Indication:** {ind}\n")
        
        if drug.get('mechanism_of_action'):
            mech = str(drug['mechanism_of_action'])[:400]
            if len(str(drug.get('mechanism_of_action', ''))) > 400:
                mech += "..."
            result.append(f"**Mechanism of Action:** {mech}\n")
        
        if drug.get('pharmacodynamics'):
            pd = str(drug['pharmacodynamics'])[:400]
            if len(str(drug.get('pharmacodynamics', ''))) > 400:
                pd += "..."
            result.append(f"**Pharmacodynamics:** {pd}\n")
        
        if drug.get('toxicity'):
            tox = str(drug['toxicity'])[:400]
            if len(str(drug.get('toxicity', ''))) > 400:
                tox += "..."
            result.append(f"**⚠️ Toxicity/Side Effects:** {tox}\n")
        
        if drug.get('half_life'):
            result.append(f"**Half-life:** {drug['half_life']}\n")
        
        if drug.get('metabolism'):
            metab = str(drug['metabolism'])[:200]
            if len(str(drug.get('metabolism', ''))) > 200:
                metab += "..."
            result.append(f"**Metabolism:** {metab}\n")
        
        if drug.get('groups'):
            groups = drug['groups'] if isinstance(drug['groups'], list) else [drug['groups']]
            result.append(f"**Groups:** {', '.join(groups)}\n")
        
        return "".join(result)
        
    except Exception as e:
        return f"Error looking up drug: {str(e)}"


@tool
def check_drug_interaction(
    drug1: Annotated[str, "First drug name"],
    drug2: Annotated[str, "Second drug name"]
) -> str:
    """
    Check if two drugs interact with each other.
    Use this tool when the user asks about:
    - Drug-drug interactions
    - Whether two medications can be taken together
    - Safety of combining two drugs
    - Potential interactions between medications
    
    Examples of questions that need this tool:
    - "Does Warfarin interact with Aspirin?"
    - "Can I take Metformin with Lisinopril?"
    - "Is it safe to combine Digoxin and Warfarin?"
    - "What happens if I take X and Y together?"
    """
    try:
        drug1 = drug1.strip()
        drug2 = drug2.strip()
        
        # Helper to resolve synonyms
        def resolve_name(name: str) -> str:
            for variant in [name, name.title(), name.upper()]:
                syn_resp = drugs_table.get_item(
                    Key={'PK': f'DRUG#{variant}', 'SK': 'SYNONYM'}
                )
                if 'Item' in syn_resp and 'points_to' in syn_resp['Item']:
                    return syn_resp['Item']['points_to']
                
                meta_resp = drugs_table.get_item(
                    Key={'PK': f'DRUG#{variant}', 'SK': 'META'}
                )
                if 'Item' in meta_resp:
                    return meta_resp['Item'].get('name', variant)
            return name
        
        resolved1 = resolve_name(drug1)
        resolved2 = resolve_name(drug2)
        
        # Try both orders with INTERACTS# prefix
        for d1, d2 in [(resolved1, resolved2), (resolved2, resolved1)]:
            for d1_var in [d1, d1.title()]:
                for d2_var in [d2, d2.title()]:
                    response = interactions_table.get_item(
                        Key={
                            'PK': f'DRUG#{d1_var}',
                            'SK': f'INTERACTS#{d2_var}'
                        }
                    )
                    
                    if 'Item' in response:
                        interaction = response['Item']
                        result = []
                        result.append(f"⚠️ **Interaction Found: {d1_var} ↔ {d2_var}**\n")
                        
                        if interaction.get('description'):
                            result.append(f"**Description:** {interaction['description']}\n")
                        
                        if interaction.get('severity'):
                            result.append(f"**Severity:** {interaction['severity']}\n")
                        
                        if interaction.get('management'):
                            result.append(f"**Management:** {interaction['management']}\n")
                        
                        result.append("\n⚠️ Always consult a healthcare professional about drug interactions.")
                        return "".join(result)
        
        return f"✅ No known interaction found between {resolved1} and {resolved2}.\n\nHowever, this doesn't mean it's safe to combine these drugs. Always consult a healthcare professional."
        
    except Exception as e:
        return f"Error checking interaction: {str(e)}"


@tool
def search_medical_documents(
    query: Annotated[str, "The medical question or topic to search for in the documents"]
) -> str:
    """
    Search through medical documents, guidelines, and PDFs using RAG (Retrieval Augmented Generation).
    Use this tool when the user asks about:
    - General medical conditions (hypoglycemia, diabetes, hypertension, etc.)
    - Treatment protocols or guidelines
    - Medical procedures or management strategies
    - Symptoms, causes, or risk factors
    - Prevention or therapy recommendations
    - Any medical question NOT specifically about a single drug's properties or drug interactions
    
    Examples of questions that need this tool:
    - "What should I do during hypoglycemia?"
    - "How to manage diabetes?"
    - "What are the symptoms of hypertension?"
    - "Treatment guidelines for heart failure"
    - "What causes insulin resistance?"
    """
    rag_chain = get_rag_chain()
    
    if rag_chain is None:
        return "RAG system is not initialized. Medical document search is unavailable. Please try asking about specific drugs instead."
    
    try:
        result = rag_chain.query(query, chain_type="qa")
        
        answer = result.get('answer', 'No answer found.')
        sources = result.get('source_documents', [])
        
        # Format response with sources
        response_parts = [answer]
        
        if sources:
            response_parts.append("\n\n📚 **Sources:**")
            seen_sources = set()
            for i, doc in enumerate(sources[:3], 1):
                source_name = doc.metadata.get('source', doc.metadata.get('file_name', 'Unknown'))
                page = doc.metadata.get('page', '')
                
                source_key = f"{source_name}_{page}"
                if source_key in seen_sources:
                    continue
                seen_sources.add(source_key)
                
                if page:
                    response_parts.append(f"\n{i}. {source_name} (Page {page})")
                else:
                    response_parts.append(f"\n{i}. {source_name}")
                
                snippet = doc.page_content[:150].strip()
                if len(doc.page_content) > 150:
                    snippet += "..."
                response_parts.append(f'\n   _"{snippet}"_')
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error searching documents: {str(e)}"


# ============================================================
# All available tools
# ============================================================

ALL_TOOLS = [get_drug_info, check_drug_interaction, search_medical_documents]


# ============================================================
# Agent Class with Tool Calling
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, an expert medical information assistant. You help users find accurate information about drugs and medical topics.

You have access to 3 tools:

1. **get_drug_info**: Use this to get detailed information about a specific drug (indications, mechanism, side effects, etc.)
   - Use when user asks: "What is X?", "Tell me about X drug", "Side effects of X", "How does X work?"

2. **check_drug_interaction**: Use this to check if two drugs interact with each other
   - Use when user asks: "Does X interact with Y?", "Can I take X with Y?", "Is it safe to combine X and Y?"

3. **search_medical_documents**: Use this to search medical guidelines and documents for general medical questions
   - Use when user asks about: conditions (diabetes, hypertension), symptoms, treatments, guidelines, management strategies
   - Examples: "What to do during hypoglycemia?", "How to manage diabetes?", "Treatment for hypertension"

IMPORTANT GUIDELINES:
- Choose the most appropriate tool based on the user's question
- For drug-specific questions → use get_drug_info
- For drug interaction questions → use check_drug_interaction  
- For general medical/health questions → use search_medical_documents
- You can use multiple tools if needed
- Always remind users to consult healthcare professionals for medical advice
- Be accurate, helpful, and clear in your responses"""


class MedicaLLMAgent:
    """LangChain Agent with Tool Calling - LLM decides which tools to use."""
    
    def __init__(
        self,
        ollama_model_name: str = "llama2",
        ollama_base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        rag_chain = None
    ):
        self.model_name = ollama_model_name
        self.base_url = ollama_base_url
        self.temperature = temperature
        
        # Set RAG chain if provided
        if rag_chain:
            set_rag_chain(rag_chain)
        
        # Initialize LLM with tool binding
        self.llm = ChatOllama(
            model=ollama_model_name,
            base_url=ollama_base_url,
            temperature=temperature
        )
        
        # Bind tools to LLM
        self.tools = ALL_TOOLS
        self.tools_dict = {t.name: t for t in self.tools}
        
        # llama2 doesn't support native tool calling, use ReAct pattern
        self.llm_with_tools = self.llm
        self.native_tool_calling = False
        print("ℹ️ Using ReAct pattern for tool calling")
        
        # Chat history
        self.chat_history: List[Dict[str, str]] = []
    
    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute a tool by name with given arguments."""
        if tool_name in self.tools_dict:
            tool = self.tools_dict[tool_name]
            try:
                return tool.invoke(tool_args)
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
        return f"Unknown tool: {tool_name}"
    
    def _react_agent_loop(self, question: str, max_iterations: int = 5) -> str:
        """ReAct pattern for models without native tool calling."""
        
        # Store sources from tool results
        self._last_sources = None
        
        react_prompt = """You are MedicaLLM, a medical assistant. You MUST use tools to answer questions.

TOOLS:
1. get_drug_info(drug_name) - Get drug information
2. check_drug_interaction(drug1, drug2) - Check drug interactions
3. search_medical_documents(query) - Search medical documents

FORMAT - You must respond exactly like this:
ACTION: tool_name
ARGS: {"key": "value"}

EXAMPLES:

User: What is Aspirin?
ACTION: get_drug_info
ARGS: {"drug_name": "Aspirin"}

User: Does Warfarin interact with Digoxin?
ACTION: check_drug_interaction
ARGS: {"drug1": "Warfarin", "drug2": "Digoxin"}

User: What should I do during hypoglycemia?
ACTION: search_medical_documents
ARGS: {"query": "what to do during hypoglycemia"}

Now answer the user's question using a tool."""
        
        messages = [
            SystemMessage(content=react_prompt),
        ]
        
        messages.append(HumanMessage(content=f"User: {question}"))
        
        for iteration in range(max_iterations):
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Check for final answer (both with and without underscore)
            final_answer_markers = ["FINAL_ANSWER:", "FINAL ANSWER:"]
            for marker in final_answer_markers:
                if marker in response_text:
                    final_answer = response_text.split(marker)[-1].strip()
                    
                    # Append sources if available (from RAG queries)
                    if self._last_sources:
                        print(f"📎 Appending sources to final answer")
                        final_answer = final_answer + "\n\n" + self._last_sources
                        self._last_sources = None  # Reset for next query
                    
                    return final_answer
            
            # Check for action
            if "ACTION:" in response_text:
                try:
                    # Parse action and args
                    action_part = response_text.split("ACTION:")[-1]
                    
                    if "ARGS:" in action_part:
                        tool_name = action_part.split("ARGS:")[0].strip()
                        args_str = action_part.split("ARGS:")[-1].strip()
                        
                        # Clean up the args string
                        if args_str.startswith("{"):
                            # Find the closing brace
                            brace_count = 0
                            end_idx = 0
                            for i, c in enumerate(args_str):
                                if c == '{':
                                    brace_count += 1
                                elif c == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break
                            args_str = args_str[:end_idx]
                        
                        tool_args = json.loads(args_str)
                        
                        # Execute tool
                        tool_result = self._execute_tool(tool_name, tool_args)
                        
                        print(f"🔧 Tool executed: {tool_name}")
                        print(f"📄 Tool result has sources: {'📚 **Sources:**' in tool_result}")
                        
                        # Extract and save sources from RAG results
                        if "📚 **Sources:**" in tool_result:
                            parts = tool_result.split("📚 **Sources:**")
                            self._last_sources = "📚 **Sources:**" + parts[1]
                            print(f"💾 Sources saved: {len(self._last_sources)} chars")
                            # Send only the answer to LLM, keep sources for final response
                            tool_result_for_llm = parts[0].strip()
                        else:
                            tool_result_for_llm = tool_result
                        
                        # Add to messages
                        messages.append(AIMessage(content=response_text))
                        messages.append(HumanMessage(content=f"OBSERVATION: {tool_result_for_llm}\n\nNow provide the FINAL_ANSWER based on this information."))
                        
                except Exception as e:
                    messages.append(AIMessage(content=response_text))
                    messages.append(HumanMessage(content=f"Error parsing action: {e}. Please try again with correct format."))
            else:
                # No action found, treat as final answer
                return response_text
        
        return "I couldn't complete the request within the allowed iterations. Please try rephrasing your question."
    
    def _native_tool_agent(self, question: str, max_iterations: int = 5) -> str:
        """Agent loop for models with native tool calling support."""
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
        ]
        
        # Add recent chat history
        for h in self.chat_history[-3:]:
            messages.append(HumanMessage(content=h["human"]))
            messages.append(AIMessage(content=h["ai"]))
        
        messages.append(HumanMessage(content=question))
        
        for iteration in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)
            
            # Check if there are tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                messages.append(response)
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    # Execute tool
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # Add tool result
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call['id']
                    ))
            else:
                # No tool calls, this is the final response
                return response.content
        
        return "I couldn't complete the request within the allowed iterations."
    
    def query(self, question: str) -> dict:
        """Process a user question using the agent."""
        try:
            if self.native_tool_calling:
                answer = self._native_tool_agent(question)
            else:
                answer = self._react_agent_loop(question)
            
            # Add to history
            self.chat_history.append({
                "human": question,
                "ai": answer
            })
            
            return {
                "answer": answer,
                "success": True
            }
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            import traceback
            traceback.print_exc()
            return {
                "answer": error_msg,
                "success": False,
                "error": str(e)
            }
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_history = []


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("Testing MedicaLLM Agent with Tool Calling")
    print("="*60)
    
    agent = MedicaLLMAgent()
    
    # Test 1: Drug Info
    print("\n📋 Test 1: Drug Info Query")
    print("-" * 40)
    result = agent.query("What is Warfarin?")
    print(result["answer"][:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""))
    
    # Test 2: Drug Interaction
    print("\n📋 Test 2: Drug Interaction Query")
    print("-" * 40)
    result = agent.query("Does Warfarin interact with Digoxin?")
    print(result["answer"][:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""))
    
    # Test 3: General Medical (RAG)
    print("\n📋 Test 3: General Medical Query (RAG)")
    print("-" * 40)
    result = agent.query("What should I do during hypoglycemia?")
    print(result["answer"][:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""))
