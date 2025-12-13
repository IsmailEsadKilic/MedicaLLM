"""
MedicaLLM Agent - LangChain Agent with Tools
Combines RAG system with Drug Database queries
Uses simple tool-calling approach for reliability
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import Optional, List, Dict, Any
import boto3
from botocore.config import Config
import json
import re

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
# RAG Chain Reference (set from main app)
# ============================================================

_rag_chain = None

def set_rag_chain(chain):
    """Set the RAG chain from the main application."""
    global _rag_chain
    _rag_chain = chain

# ============================================================
# Tool Functions
# ============================================================

def get_drug_info(drug_name: str) -> str:
    """Get detailed information about a drug from DynamoDB."""
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
            return f"Drug '{drug_name}' not found in database. Try using the exact drug name."
        
        # Format the response
        result = []
        result.append(f"📋 **{drug.get('name', drug_name)}**\n")
        
        if drug.get('description'):
            desc = drug['description'][:600] + "..." if len(str(drug.get('description', ''))) > 600 else drug.get('description', '')
            result.append(f"**Description:** {desc}\n")
        
        if drug.get('indication'):
            ind = drug['indication'][:500] + "..." if len(str(drug.get('indication', ''))) > 500 else drug.get('indication', '')
            result.append(f"**Indication:** {ind}\n")
        
        if drug.get('pharmacodynamics'):
            pd = drug['pharmacodynamics'][:400] + "..." if len(str(drug.get('pharmacodynamics', ''))) > 400 else drug.get('pharmacodynamics', '')
            result.append(f"**Pharmacodynamics:** {pd}\n")
        
        if drug.get('mechanism_of_action'):
            mech = drug['mechanism_of_action'][:400] + "..." if len(str(drug.get('mechanism_of_action', ''))) > 400 else drug.get('mechanism_of_action', '')
            result.append(f"**Mechanism of Action:** {mech}\n")
        
        if drug.get('toxicity'):
            tox = drug['toxicity'][:400] + "..." if len(str(drug.get('toxicity', ''))) > 400 else drug.get('toxicity', '')
            result.append(f"**⚠️ Toxicity/Side Effects:** {tox}\n")
        
        if drug.get('half_life'):
            result.append(f"**Half-life:** {drug['half_life']}\n")
        
        if drug.get('metabolism'):
            result.append(f"**Metabolism:** {drug['metabolism'][:200]}...\n" if len(str(drug.get('metabolism', ''))) > 200 else f"**Metabolism:** {drug.get('metabolism', '')}\n")
        
        if drug.get('groups'):
            groups = drug['groups'] if isinstance(drug['groups'], list) else [drug['groups']]
            result.append(f"**Groups:** {', '.join(groups)}\n")
        
        return "".join(result)
        
    except Exception as e:
        return f"Error looking up drug: {str(e)}"


def check_drug_interaction(drug1: str, drug2: str) -> str:
    """Check for interactions between two drugs."""
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
                
                # Check if META exists directly
                meta_resp = drugs_table.get_item(
                    Key={'PK': f'DRUG#{variant}', 'SK': 'META'}
                )
                if 'Item' in meta_resp:
                    return meta_resp['Item'].get('name', variant)
            return name
        
        resolved1 = resolve_name(drug1)
        resolved2 = resolve_name(drug2)
        
        # Try both orders with INTERACTS# prefix (based on actual DB structure)
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


def search_medical_docs(question: str) -> str:
    """Search through medical documents using RAG with sources."""
    if _rag_chain is None:
        return "RAG system is not initialized. Medical document search is unavailable."
    
    try:
        result = _rag_chain.query(question, chain_type="qa")
        
        answer = result.get('answer', 'No answer found.')
        sources = result.get('source_documents', [])
        
        # Format response with sources
        response_parts = [answer]
        
        if sources:
            response_parts.append("\n\n📚 **Sources:**")
            seen_sources = set()
            for i, doc in enumerate(sources[:3], 1):
                # Get source metadata
                source_name = doc.metadata.get('source', doc.metadata.get('file_name', 'Unknown'))
                page = doc.metadata.get('page', '')
                
                # Avoid duplicate sources
                source_key = f"{source_name}_{page}"
                if source_key in seen_sources:
                    continue
                seen_sources.add(source_key)
                
                # Format source info
                if page:
                    response_parts.append(f"\n{i}. {source_name} (Page {page})")
                else:
                    response_parts.append(f"\n{i}. {source_name}")
                
                # Add snippet
                snippet = doc.page_content[:150].strip()
                if len(doc.page_content) > 150:
                    snippet += "..."
                response_parts.append(f"\n   _\"{snippet}\"_")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error searching documents: {str(e)}"


# ============================================================
# MedicaLLM Agent Class
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, a helpful medical information assistant. You help users find information about drugs and medical topics.

AVAILABLE TOOLS:
1. DRUG_INFO - Get detailed information about a specific drug
2. DRUG_INTERACTION - Check for interactions between two drugs  
3. RAG_SEARCH - Search medical documents

WHEN TO USE TOOLS:
- Questions like "What is X?", "Tell me about X drug", "Side effects of X" → Use DRUG_INFO
- Questions like "Can I take X with Y?", "Do X and Y interact?" → Use DRUG_INTERACTION
- General medical questions → Use RAG_SEARCH or answer from your knowledge

RESPONSE FORMAT FOR TOOL CALLS:
When you need to use a tool, respond EXACTLY like this:
```
TOOL: DRUG_INFO
INPUT: {"drug_name": "Warfarin"}
```
or
```
TOOL: DRUG_INTERACTION
INPUT: {"drug1": "Warfarin", "drug2": "Aspirin"}
```
or
```
TOOL: RAG_SEARCH
INPUT: {"question": "What are NSAIDs?"}
```

If you can answer directly without a tool, just respond normally.

IMPORTANT REMINDERS:
- Always remind users to consult healthcare professionals for medical advice
- Be accurate and helpful
- If a drug is not found, suggest checking the spelling"""


class MedicaLLMAgent:
    """Main agent class that combines RAG and Drug Database tools."""
    
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
        
        # Initialize LLM
        self.llm = ChatOllama(
            model=ollama_model_name,
            base_url=ollama_base_url,
            temperature=temperature
        )
        
        # Chat history
        self.chat_history: List[Dict[str, str]] = []
        
        # Tool mapping
        self.tools = {
            "DRUG_INFO": self._tool_drug_info,
            "DRUG_INTERACTION": self._tool_drug_interaction,
            "RAG_SEARCH": self._tool_rag_search
        }
    
    def _tool_drug_info(self, params: dict) -> str:
        drug_name = params.get("drug_name", "")
        return get_drug_info(drug_name)
    
    def _tool_drug_interaction(self, params: dict) -> str:
        drug1 = params.get("drug1", "")
        drug2 = params.get("drug2", "")
        return check_drug_interaction(drug1, drug2)
    
    def _tool_rag_search(self, params: dict) -> str:
        question = params.get("question", "")
        return search_medical_docs(question)
    
    def _parse_tool_call(self, response: str) -> tuple:
        """Parse tool call from LLM response."""
        # Look for TOOL: and INPUT: patterns
        tool_match = re.search(r'TOOL:\s*(\w+)', response, re.IGNORECASE)
        input_match = re.search(r'INPUT:\s*(\{[^}]+\})', response, re.IGNORECASE | re.DOTALL)
        
        if tool_match and input_match:
            tool_name = tool_match.group(1).upper()
            try:
                # Clean up the JSON
                json_str = input_match.group(1).strip()
                params = json.loads(json_str)
                return tool_name, params
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return None, None
        return None, None
    
    def _detect_intent(self, question: str) -> tuple:
        """Simple intent detection based on keywords."""
        q_lower = question.lower()
        
        # List of known drug names for better detection
        known_drugs = ['warfarin', 'metformin', 'lisinopril', 'digoxin', 'aspirin', 'ibuprofen',
                       'amoxicillin', 'atorvastatin', 'omeprazole', 'losartan', 'gabapentin',
                       'prednisone', 'diazepam', 'clonazepam', 'sertraline', 'insulin']
        
        # Common words to exclude from drug name extraction
        exclude_words = ['can', 'does', 'what', 'how', 'is', 'the', 'and', 'with', 'do', 'if', 'i',
                        'take', 'have', 'are', 'there', 'any', 'between', 'for', 'about', 'this']
        
        # First, extract known drugs from the question
        found_drugs = []
        for drug in known_drugs:
            if drug in q_lower:
                found_drugs.append(drug.title())
        
        # Drug interaction patterns
        interaction_patterns = [
            r'interact',
            r'take .+ with',
            r'combine',
            r'together',
            r'.+ and .+ (safe|ok|okay)',
        ]
        
        for pattern in interaction_patterns:
            if re.search(pattern, q_lower):
                # If we found 2+ known drugs, use them
                if len(found_drugs) >= 2:
                    return "DRUG_INTERACTION", {"drug1": found_drugs[0], "drug2": found_drugs[1]}
                
                # Otherwise extract capitalized words that aren't common words
                drugs = re.findall(r'\b([A-Z][a-z]+)\b', question)
                drugs = [d for d in drugs if d.lower() not in exclude_words]
                if len(drugs) >= 2:
                    return "DRUG_INTERACTION", {"drug1": drugs[0], "drug2": drugs[1]}
        
        # Check if question mentions a known drug specifically
        mentioned_drug = found_drugs[0] if found_drugs else None
        
        # Single drug info patterns - only if asking about a specific drug
        drug_info_patterns = [
            r'what is (\w+)\??$',
            r'tell me about (\w+)',
            r'information (on|about) (\w+)',
            r'side effects (of )?(\w+)',
            r'(\w+) used for',
            r'how does (\w+) work',
            r'dosage (of|for) (\w+)',
        ]
        
        for pattern in drug_info_patterns:
            match = re.search(pattern, q_lower)
            if match:
                groups = match.groups()
                drug = None
                for g in groups:
                    if g and g not in ['on', 'about', 'of', 'for']:
                        drug = g
                        break
                if drug and drug.lower() not in ['this', 'that', 'it', 'the', 'a', 'an', 'i', 'you']:
                    # Check if it looks like a drug name (capitalized or known)
                    if drug.lower() in known_drugs or mentioned_drug:
                        return "DRUG_INFO", {"drug_name": drug.title()}
        
        # If a known drug is mentioned but pattern didn't match, still use DRUG_INFO
        if mentioned_drug:
            return "DRUG_INFO", {"drug_name": mentioned_drug}
        
        # General medical/health questions -> RAG
        medical_keywords = [
            'hypoglycemia', 'hyperglycemia', 'diabetes', 'hypertension', 'blood pressure',
            'symptoms', 'treatment', 'diagnosis', 'disease', 'condition', 'syndrome',
            'what can i do', 'how to treat', 'how to manage', 'what should i',
            'during', 'when', 'signs of', 'causes of', 'risk factors',
            'prevention', 'therapy', 'medication', 'medicine',
        ]
        
        for keyword in medical_keywords:
            if keyword in q_lower:
                return "RAG_SEARCH", {"question": question}
        
        # Default: if question mark and medical-sounding, try RAG
        if '?' in question and any(word in q_lower for word in ['what', 'how', 'why', 'when', 'should']):
            return "RAG_SEARCH", {"question": question}
        
        return None, None
    
    def query(self, question: str) -> dict:
        """Process a user question."""
        try:
            # First, try simple intent detection
            detected_tool, detected_params = self._detect_intent(question)
            
            if detected_tool and detected_tool in self.tools:
                # Execute detected tool directly
                tool_result = self.tools[detected_tool](detected_params)
                
                # Format nice response
                answer = f"{tool_result}"
                
                self.chat_history.append({
                    "human": question,
                    "ai": answer
                })
                
                return {
                    "answer": answer,
                    "success": True,
                    "tool_used": detected_tool
                }
            
            # If no clear intent, use LLM
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            
            # Add chat history (last 3 exchanges)
            for h in self.chat_history[-3:]:
                messages.append(HumanMessage(content=h["human"]))
                messages.append(AIMessage(content=h["ai"]))
            
            messages.append(HumanMessage(content=question))
            
            # Get LLM response
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Check if LLM wants to use a tool
            tool_name, params = self._parse_tool_call(response_text)
            
            if tool_name and tool_name in self.tools:
                # Execute tool
                tool_result = self.tools[tool_name](params)
                
                # Get final response with tool result
                messages.append(AIMessage(content=response_text))
                messages.append(HumanMessage(content=f"Tool Result:\n{tool_result}\n\nBased on this information, provide a helpful response to the user. Do not use tool format again."))
                
                final_response = self.llm.invoke(messages)
                answer = final_response.content
            else:
                answer = response_text
            
            # Clean up any tool call artifacts from the answer
            answer = re.sub(r'```\s*TOOL:.*?```', '', answer, flags=re.DOTALL)
            answer = re.sub(r'TOOL:\s*\w+\s*INPUT:\s*\{[^}]+\}', '', answer)
            
            # Add to history
            self.chat_history.append({
                "human": question,
                "ai": answer
            })
            
            return {
                "answer": answer.strip(),
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
# Direct Tool Access (for API endpoints)
# ============================================================

def direct_drug_query(drug_name: str) -> dict:
    """Direct drug query without LLM - for API endpoints."""
    result = get_drug_info(drug_name)
    return {
        "drug_name": drug_name,
        "info": result,
        "success": "not found" not in result.lower()
    }


def direct_interaction_check(drug1: str, drug2: str) -> dict:
    """Direct interaction check without LLM - for API endpoints."""
    result = check_drug_interaction(drug1, drug2)
    has_interaction = "interaction found" in result.lower()
    return {
        "drug1": drug1,
        "drug2": drug2,
        "result": result,
        "has_interaction": has_interaction
    }


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("Testing MedicaLLM Agent...")
    print("="*60)
    
    # Test direct functions first (no LLM needed)
    print("\n📋 Test 1: Direct Drug Info Query")
    result = get_drug_info("Warfarin")
    print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n" + "="*60)
    print("📋 Test 2: Direct Interaction Check")
    result = check_drug_interaction("Warfarin", "Digoxin")
    print(result)
    
    print("\n" + "="*60)
    print("📋 Test 3: Agent Query (requires Ollama)")
    try:
        agent = MedicaLLMAgent()
        result = agent.query("What is Metformin used for?")
        print(result["answer"][:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""))
    except Exception as e:
        print(f"Agent test skipped (Ollama may not be running): {e}")
