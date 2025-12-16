from typing import Annotated, Optional
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_aws import ChatBedrock
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
        
        pm.ins(result, message="Drug info retrieved")
        
        if not result.get('success'):
            return f"Drug not found: {drug_name}"
        
        # Build simple, natural description for LLM to process
        parts = []
        
        drug_name_display = result['drug_name']
        if result.get('is_synonym'):
            parts.append(f"{result['queried_name']} (also known as {result['actual_name']})")
            drug_name_display = result['actual_name']
        else:
            parts.append(drug_name_display)
        
        if result.get('indication') != 'N/A':
            parts.append(f"Indication: {result['indication']}")
        
        if result.get('mechanism_of_action') != 'N/A':
            parts.append(f"Mechanism: {result['mechanism_of_action']}")
        
        if result.get('toxicity') != 'N/A':
            parts.append(f"Side effects/toxicity: {result['toxicity']}")
        
        if result.get('metabolism') != 'N/A':
            parts.append(f"Metabolism: {result['metabolism']}")
        
        if result.get('half_life') != 'N/A':
            parts.append(f"Half-life: {result['half_life']}")
        
        return " | ".join(parts)
        
    except Exception as e:
        pm.err(e=e, m=f"Error in get_drug_info for '{drug_name}'")
        return f"❌ Error retrieving drug information: {str(e)}"


# ============================================================
# TOOL 3: Drug-Food Interaction Check
# ============================================================

@tool
def check_drug_food_interaction(
    drug_name: Annotated[str, "Name of the drug"]
) -> str:
    """
    Check if a drug has any food interactions or dietary restrictions.
    
    Use this when the user asks about:
    - Food interactions with a drug
    - What to eat or avoid while taking a medication
    - Dietary restrictions for a drug
    - Whether to take a drug with or without food
    
    Examples:
    - "Can I eat grapefruit with Warfarin?"
    - "Should I take Metformin with food?"
    - "Are there any food restrictions for Lisinopril?"
    - "What foods should I avoid with this medication?"
    """
    try:
        pm.inf(f"🔍 Checking food interactions for: {drug_name}")
        result = db_manager.get_drug_food_interactions(drug_name)
        
        if not result.get('success'):
            return f"❌ Error checking food interactions: {result.get('error', 'Unknown error')}"
        
        if result.get('count', 0) > 0:
            interactions = result['interactions']
            response = [
                f"🍽️ **Food Interactions for {result['drug_name']}**",
                f"\nFound {result['count']} food interaction(s):\n"
            ]
            
            for i, interaction in enumerate(interactions, 1):
                response.append(f"{i}. {interaction}")
            
            response.append(
                "\n⚕️ **Important:** Always follow your healthcare provider's instructions "
                "regarding food and medication timing."
            )
            return "\n".join(response)
        else:
            return (
                f"✅ **No Food Interactions Documented**\n\n"
                f"No specific food interactions are documented for {result['drug_name']} "
                f"in our database.\n\n"
                f"⚕️ **Note:** This doesn't mean there are no interactions. Always consult "
                f"your healthcare provider or pharmacist about dietary considerations."
            )
            
    except Exception as e:
        pm.err(e=e, m=f"Error checking food interactions for '{drug_name}'")
        return f"❌ Error checking food interactions: {str(e)}"


# ============================================================
# TOOL 4: Search Drugs by Category/Indication
# ============================================================

@tool
def search_drugs_by_indication(
    condition: Annotated[str, "Medical condition or therapeutic category (e.g., diabetes, hypertension, pain)"]
) -> str:
    """
    Search for drugs in the database that treat a specific condition or belong to a therapeutic category.
    
    Use this when the user asks about:
    - What drugs treat a condition
    - Alternative medications for a condition
    - Drug recommendations for a specific disease
    - Medications available for a therapeutic purpose
    
    Examples:
    - "What drugs treat diabetes?"
    - "Recommend alternatives for hypertension"
    - "What medications are available for pain?"
    - "Show me drugs for blood glucose control"
    """
    try:
        pm.inf(f"🔍 Searching drugs for condition: {condition}")
        result = db_manager.search_drugs_by_category(condition, limit=10)
        
        if not result.get('success'):
            return f"❌ Error searching drugs: {result.get('error', 'Unknown error')}"
        
        if result.get('count', 0) == 0:
            return f"❌ No drugs found in our database for '{condition}'. Try different keywords like 'diabetes', 'hypertension', or 'pain'."
        
        drugs = result['drugs']
        response = [
            f"💊 **Found {result['count']} drug(s) for {condition}:**\n"
        ]
        
        for i, drug in enumerate(drugs, 1):
            response.append(f"{i}. **{drug['name']}**")
            if drug.get('categories'):
                response.append(f"   Categories: {', '.join(drug['categories'])}")
            if drug.get('indication') and drug['indication'] != 'N/A':
                indication = drug['indication'][:150]
                if len(drug['indication']) > 150:
                    indication += "..."
                response.append(f"   Indication: {indication}")
            response.append("")
        
        response.append("⚕️ **Note:** Consult your healthcare provider before starting any medication.")
        return "\n".join(response)
        
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs for '{condition}'")
        return f"❌ Error searching drugs: {str(e)}"


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
        pm.inf(f"🔍 [TOOL] check_drug_interaction called with: drug1='{drug1}', drug2='{drug2}'")
        result = db_manager.check_drug_interaction(drug1, drug2)
        
        pm.inf(f"📊 [TOOL] DB result: {result}")
        
        if not result.get('success'):
            error_msg = f"❌ Error checking interaction: {result.get('error', 'Unknown error')}"
            pm.err(m=f"[TOOL] Returning error: {error_msg}")
            return error_msg
        
        if result.get('interaction_found'):
            # Return simple data for LLM to process naturally
            response = f"Yes, {result['drug1']} and {result['drug2']} do interact. {result['description']} It's important to consult with a healthcare provider before taking these medications together."
            pm.suc(f"✅ [TOOL] Returning interaction data ({len(response)} chars)")
            return response
        else:
            response = f"No documented interaction found between {result['drug1']} and {result['drug2']}. However, always inform your healthcare provider about all medications you're taking."
            pm.suc(f"✅ [TOOL] Returning no interaction data ({len(response)} chars)")
            return response
            
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
        
        # Use ChatBedrock to generate answer from context
        llm = ChatBedrock(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            model_kwargs={"temperature": 0.3, "max_tokens": 2048}
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
4. **search_medical_documents** - Search medical guidelines

INTERACTION RESPONSE TEMPLATE:

When checking drug interactions, your response MUST include these parts in order:

1. **Direct answer**: "Yes, [Drug1] and [Drug2] do interact" or "No interaction found"
2. **What happens**: Explain the specific interaction from the tool data
3. **Why it matters**: What could this mean for the patient
4. **Action needed**: Consult healthcare provider

EXAMPLE - CORRECT Interaction Response:
User: "Does Warfarin interact with Ibuprofen?"

Tool returns: "Yes, Warfarin and Ibuprofen do interact. Ibuprofen may decrease the excretion rate of Warfarin which could result in a higher serum level. It's important to consult with a healthcare provider before taking these medications together."

Your response should be:
"Yes, Warfarin and Ibuprofen do interact. Specifically, Ibuprofen can decrease how quickly Warfarin is eliminated from your body, which could result in higher Warfarin levels in your bloodstream. This means there's an increased risk of bleeding complications.

⚠️ **Important**: Please consult with your healthcare provider before taking these medications together. They may need to monitor your INR more closely, adjust your Warfarin dosage, or recommend an alternative pain reliever."

EXAMPLE - WRONG (missing interaction details):
"Please consult your healthcare provider before taking these together." ❌ (Missing WHAT the interaction is!)

Remember: ALWAYS explain WHAT the interaction is before giving warnings."""


# ============================================================
# Agent Creation Function
# ============================================================

def create_medical_agent(
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    temperature: float = 0.3,
    retriever: Optional[VectorStoreRetriever] = None
):
    """
    Create a MedicaLLM agent using LangChain's create_agent.
    
    Args:
        bedrock_model_id: AWS Bedrock model ID to use
        temperature: Model temperature (0-1)
        retriever: Optional vector store retriever for RAG functionality
        
    Returns:
        A LangChain agent ready to process medical queries
    """
    # Set retriever if provided
    if retriever:
        set_retriever(retriever)
    
    # Initialize the model
    model = ChatBedrock(
        model_id=bedrock_model_id,
        model_kwargs={"temperature": temperature, "max_tokens": 4096}
    )
    
    # Define tools
    tools = [get_drug_info, check_drug_interaction, check_drug_food_interaction, search_medical_documents]
    
    # Create the agent using LangChain's create_agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )
    
    pm.suc(f"✅ MedicaLLM Agent created with model: {bedrock_model_id}")
    
    return agent