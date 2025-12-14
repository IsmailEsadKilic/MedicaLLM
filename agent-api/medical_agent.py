from typing import Annotated, Optional
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
import printmeup as pm

from dynamodb_manager import DynamoDBManager

# ============================================================
# Initialize DynamoDB Manager
# ============================================================

db_manager = DynamoDBManager()
_retriever: Optional[VectorStoreRetriever] = None
_last_search_sources = None  # Store sources from last search


def set_retriever(retriever: VectorStoreRetriever):
    """Set the vector store retriever for RAG tool."""
    global _retriever
    _retriever = retriever
    pm.suc("✅ Retriever set for medical document search")


def get_retriever() -> Optional[VectorStoreRetriever]:
    """Get the current retriever."""
    return _retriever


def get_last_search_sources():
    """Get and clear the last search sources."""
    global _last_search_sources
    sources = _last_search_sources
    _last_search_sources = None
    return sources

# ============================================================
# TOOL 1: Drug Information Lookup
# ============================================================

@tool
def get_drug_info(drug_name: Annotated[str, "Name of the drug (e.g., Warfarin, Metformin, Aspirin)"]) -> str:
    """
    Get comprehensive information about a specific drug from the database.
    
    Use this when the user asks about:
    - What a drug is or what it does
    - Drug indications (what it treats)
    - How a drug works (mechanism of action)
    - Side effects or toxicity
    - Pharmacokinetics (absorption, metabolism, half-life, etc.)
    - Drug properties and characteristics
    
    Examples:
    - "What is Warfarin?"
    - "Tell me about Metformin"
    - "What are the side effects of Aspirin?"
    - "How does Lisinopril work?"
    """
    try:
        pm.inf(f"🔍 Looking up drug: {drug_name}")
        result = db_manager.get_drug_info(drug_name)
        
        if not result.get('success'):
            return f"❌ Drug not found: {drug_name}"
        
        # Format response
        response_parts = []
        
        # Handle synonym case
        if result.get('is_synonym'):
            response_parts.append(
                f"📝 Note: '{result['queried_name']}' is listed in our database as '{result['actual_name']}'.\n"
            )
        
        # Basic info
        response_parts.append(f"**Drug Name:** {result['drug_name']}")
        if result.get('drug_id'):
            response_parts.append(f"**DrugBank ID:** {result['drug_id']}")
        
        # Clinical information
        if result.get('indication') != 'N/A':
            response_parts.append(f"\n**Indication:**\n{result['indication']}")
        
        if result.get('mechanism_of_action') != 'N/A':
            response_parts.append(f"\n**Mechanism of Action:**\n{result['mechanism_of_action']}")
        
        if result.get('pharmacodynamics') != 'N/A':
            response_parts.append(f"\n**Pharmacodynamics:**\n{result['pharmacodynamics']}")
        
        # Safety information
        if result.get('toxicity') != 'N/A':
            response_parts.append(f"\n**Toxicity & Side Effects:**\n{result['toxicity']}")
        
        # Pharmacokinetics
        pk_info = []
        if result.get('absorption') != 'N/A':
            pk_info.append(f"- **Absorption:** {result['absorption']}")
        if result.get('metabolism') != 'N/A':
            pk_info.append(f"- **Metabolism:** {result['metabolism']}")
        if result.get('half_life') != 'N/A':
            pk_info.append(f"- **Half-life:** {result['half_life']}")
        if result.get('protein_binding') != 'N/A':
            pk_info.append(f"- **Protein Binding:** {result['protein_binding']}")
        
        if pk_info:
            response_parts.append("\n**Pharmacokinetics:**")
            response_parts.extend(pk_info)
        
        # Additional properties
        if result.get('groups'):
            response_parts.append(f"\n**Drug Groups:** {', '.join(result['groups'])}")
        
        if result.get('categories'):
            categories = result['categories'][:5]  # Limit to first 5
            response_parts.append(f"\n**Categories:** {', '.join(categories)}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        pm.err(e=e, m=f"Error in get_drug_info for '{drug_name}'")
        return f"❌ Error retrieving drug information: {str(e)}"


# ============================================================
# TOOL 2: Drug Interaction Check
# ============================================================

@tool
def check_drug_interaction(
    drug1: Annotated[str, "First drug name"],
    drug2: Annotated[str, "Second drug name"]
) -> str:
    """
    Check if two drugs have a known interaction.
    
    Use this when the user asks about:
    - Drug-drug interactions
    - Safety of combining medications
    - Whether two drugs can be taken together
    
    Examples:
    - "Does Warfarin interact with Ibuprofen?"
    - "Can I take Lisinopril with Aspirin?"
    - "Are there any interactions between Metformin and Glipizide?"
    """
    try:
        pm.inf(f"🔍 Checking interaction: {drug1} + {drug2}")
        result = db_manager.check_drug_interaction(drug1, drug2)
        
        if not result.get('success'):
            return f"❌ Error checking interaction: {result.get('error', 'Unknown error')}"
        
        if result.get('interaction_found'):
            response = [
                "⚠️ **Interaction Found**",
                f"\n**Drug 1:** {result['drug1']}",
                f"**Drug 2:** {result['drug2']}",
                f"\n**Description:**\n{result['description']}",
                "\n⚕️ **Important:** Consult with your healthcare provider before taking these medications together."
            ]
            return "\n".join(response)
        else:
            return (
                f"✅ **No Known Interaction**\n\n"
                f"No documented interaction found between {result['drug1']} and {result['drug2']} "
                f"in our database.\n\n"
                f"⚕️ **Note:** This doesn't guarantee absolute safety. Always consult your healthcare "
                f"provider before combining medications."
            )
            
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        return f"❌ Error checking interaction: {str(e)}"


# ============================================================
# TOOL 3: Medical Document Search (RAG)
# ============================================================

@tool
def search_medical_documents(
    query: Annotated[str, "Medical question or topic to search for"]
) -> str:
    """
    Search through medical documents, guidelines, and clinical resources using RAG.
    
    Use this when the user asks about:
    - General medical conditions (diabetes, hypertension, etc.)
    - Treatment protocols or clinical guidelines
    - Medical procedures or management strategies
    - Symptoms, causes, or risk factors
    - Prevention or therapy recommendations
    - Any medical topic NOT about a specific drug's properties or drug interactions
    
    Examples:
    - "What should I do during hypoglycemia?"
    - "How to manage type 2 diabetes?"
    - "What are the symptoms of hypertension?"
    - "Treatment guidelines for heart failure"
    """
    global _last_search_sources
    retriever = get_retriever()
    
    if retriever is None:
        return (
            "📚 Medical document search is currently unavailable. "
            "I can still help with drug information and interactions."
        )
    
    try:
        pm.inf(f"📚 Searching medical documents for: {query}")
        
        # Retrieve relevant documents
        docs = retriever.invoke(query)
        
        if not docs:
            _last_search_sources = None
            return "❌ No relevant medical documents found for your query."
        
        # Store sources globally for session to retrieve
        _last_search_sources = [
            {
                "source": doc.metadata.get('source', doc.metadata.get('file_name', 'Unknown')),
                "page": doc.metadata.get('page', ''),
                "content": doc.page_content[:200]
            }
            for doc in docs[:3]
        ]
        
        # Format the context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use ChatOllama to generate answer from context
        llm = ChatOllama(
            model="llama2:latest",
            base_url="http://localhost:11434",
            temperature=0.3
        )
        
        prompt = f"""Based on the following medical information, answer this question: {query}

Medical Information:
{context}

Provide a comprehensive, accurate answer based solely on the information provided above. If the information doesn't contain a clear answer, say so."""
        
        response = llm.invoke(prompt)
        answer = response.content if isinstance(response.content, str) else str(response.content)
        
        # Add sources
        response_parts = [answer]
        response_parts.append("\n\n📚 **Sources:**")
        
        seen_sources = set()
        for i, doc in enumerate(docs[:3], 1):  # Limit to top 3 sources
            source_name = doc.metadata.get('source', doc.metadata.get('file_name', 'Unknown'))
            page = doc.metadata.get('page', '')
            
            source_key = f"{source_name}_{page}"
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)
            
            if page:
                response_parts.append(f"{i}. {source_name} (Page {page})")
            else:
                response_parts.append(f"{i}. {source_name}")
            
            # Add snippet
            snippet = doc.page_content[:150].strip()
            if len(doc.page_content) > 150:
                snippet += "..."
            response_parts.append(f'   _"{snippet}"_')
        
        return "\n".join(response_parts)
        
    except Exception as e:
        pm.err(e=e, m=f"Error searching documents for '{query}'")
        return f"❌ Error searching documents: {str(e)}"

# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, an expert medical information assistant specialized in drug information and medical knowledge.

You have access to 3 powerful tools:

1. **get_drug_info**: Get detailed drug information (indications, mechanism, side effects, pharmacokinetics)
   - Use when asked: "What is X?", "Tell me about X drug", "Side effects of X", "How does X work?"

2. **check_drug_interaction**: Check if two drugs interact
   - Use when asked: "Does X interact with Y?", "Can I take X with Y?", "Is it safe to combine X and Y?"

3. **search_medical_documents**: Search medical guidelines and documents
   - Use for: conditions, symptoms, treatments, clinical guidelines, management strategies
   - Examples: "What to do during hypoglycemia?", "How to manage diabetes?", "Treatment for hypertension"

IMPORTANT GUIDELINES:
- **Use tools** - Don't rely on training data for drug information. You dont need to use tools for non-medical questions.
- **Be accurate** - Medical information must be precise and up-to-date
- **Be helpful** - Provide comprehensive answers with proper formatting
- **Be safe** - Always remind users to consult healthcare professionals
- **Handle synonyms** - If a drug name is a synonym, explain the database mapping clearly
- **Use markdown** - Format responses with **bold**, bullets, and sections for readability

When answering:
1. Choose the right tool for the question
2. Parse tool results carefully
3. Present information clearly with proper formatting
4. Always include safety disclaimers for medical advice

Remember: You are an information assistant, not a replacement for professional medical advice."""


# ============================================================
# Agent Creation Function
# ============================================================

def create_medical_agent(
    ollama_model_name: str = "llama2:latest",
    ollama_base_url: str = "http://localhost:11434",
    temperature: float = 0.3,
    retriever: Optional[VectorStoreRetriever] = None
):
    """
    Create a MedicaLLM agent using LangChain's create_agent.
    
    Args:
        ollama_model_name: Name of the Ollama model to use
        ollama_base_url: Base URL for Ollama API
        temperature: Model temperature (0-1)
        retriever: Optional vector store retriever for RAG functionality
        
    Returns:
        A LangChain agent ready to process medical queries
    """
    # Set retriever if provided
    if retriever:
        set_retriever(retriever)
    
    # Initialize the model
    model = ChatOllama(
        model=ollama_model_name,
        base_url=ollama_base_url,
        temperature=temperature
    )
    
    # Define tools
    tools = [get_drug_info, check_drug_interaction, search_medical_documents]
    
    # Create the agent using LangChain's create_agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )
    
    pm.suc(f"✅ MedicaLLM Agent created with model: {ollama_model_name}")
    
    return agent