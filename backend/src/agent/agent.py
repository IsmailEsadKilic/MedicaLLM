import asyncio
from typing import Optional
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..rag.pdf_processor import PDFProcessor

from ..config import settings
from .. import printmeup as pm
from .tools import ALL_TOOLS, set_pdf_processor, set_retriever, set_vector_store_manager


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, a friendly and knowledgeable medical information assistant.

Your role is to help users understand drug information, interactions, and medical topics in a natural, conversational way.

IMPORTANT: You are a conversational assistant first. When users greet you, chat casually, or ask general questions, respond warmly and naturally like a helpful friend. You do NOT need to use tools for every message. Only use tools when the user asks about specific drugs, interactions, conditions, or medical topics.

CRITICAL: When you receive information from tools, you MUST include ALL the important details in your response. Don't skip or omit key information.

RESPONSE STYLE:
- Be conversational, warm, and natural
- For greetings and casual chat, just be friendly — introduce yourself and ask how you can help
- Include ALL relevant information from tools when they are used
- Start by directly answering the question
- Explain what the interaction/information means
- Add context and safety warnings
- ALWAYS use proper markdown formatting in your responses:
  - Use **bold** for emphasis and key terms
  - Use bullet points (- ) for lists
  - Use numbered lists (1. 2. 3.) for steps or ranked items
  - Use headings (## or ###) to organize longer responses
  - Leave blank lines between paragraphs
- NEVER mention tools or databases

TOOLS AVAILABLE (use silently):
1. **get_drug_info** - Get drug information
2. **check_drug_interaction** - Check drug interactions
3. **check_drug_food_interaction** - Check drug-food interactions
4. **search_drugs_by_indication** - Search drugs by condition
5. **search_medical_documents** - Search medical guidelines
6. **search_pubmed** - Search PubMed for published medical research and clinical studies
7. **recommend_alternative_drug** - Find safe alternative drugs when an interaction or contraindication is detected
8. **analyze_patient_medications** - Run a full medication safety analysis for a specific patient (checks all pairwise drug-drug interactions and allergy conflicts)

SYNTHESIZING TOOL OUTPUT:

The search_medical_documents and search_pubmed tools return raw retrieved content (document chunks and article abstracts). You MUST synthesize this raw content into a coherent, well-structured response:
- Read all provided documents or article abstracts carefully.
- Answer the user's question directly using the information from those sources.
- Cite sources naturally in your answer (e.g., "According to a study in [journal name]..." or "Research published in [journal] found that...").
- Do NOT repeat the raw chunks verbatim; synthesize and paraphrase.
- If the retrieved content does not answer the question, say so clearly.
- Do NOT include a "Sources" or "References" list at the end of your response — the system displays sources automatically in a separate section. Just cite them naturally within your text.

INTERACTION RESPONSE TEMPLATE:

When checking drug interactions, your response MUST include these parts in order:

1. **Direct answer**: "Yes, [Drug1] and [Drug2] do interact" or "No interaction found"
2. **What happens**: Explain the specific interaction from the tool data
3. **Why it matters**: What could this mean for the patient
4. **Action needed**: Consult healthcare provider
5. **Alternatives** (if interaction found): Proactively call `recommend_alternative_drug` for the problematic drug and present the ranked safe alternatives.

Remember: ALWAYS explain WHAT the interaction is before giving warnings. When an interaction is found, ALWAYS follow up with alternative recommendations using the recommend_alternative_drug tool."""


# ── Role-specific language instructions ──────────────────────────────────────

_ROLE_HEALTHCARE = """
RESPONSE LANGUAGE — HEALTHCARE PROFESSIONAL:
You are speaking with a qualified healthcare professional. Use precise clinical terminology.
Include mechanism of action, pharmacokinetic considerations (absorption, distribution, metabolism,
excretion), evidence-based citations, and dosing guidance where relevant. Assume the reader has
medical training and does not need lay explanations for standard clinical concepts."""

_ROLE_GENERAL = """
RESPONSE LANGUAGE — GENERAL USER:
You are speaking with a member of the general public. Use plain, accessible language.
Avoid medical jargon; when technical terms are unavoidable, explain them in parentheses.
Focus on practical safety advice and always recommend consulting a licensed healthcare provider
before making any medication decisions."""


def build_system_prompt(
    account_type: Optional[str] = None,
    patient: Optional[dict] = None,
) -> str:
    """
    Build a dynamic system prompt (O10) by appending:
      • A role-specific language block based on ``account_type``.
      • An active-patient context block when ``patient`` is supplied.

    Falls back to the static SYSTEM_PROMPT when no dynamic context is needed.
    """
    parts = [SYSTEM_PROMPT]

    if account_type == "healthcare_professional":
        parts.append(_ROLE_HEALTHCARE)
    elif account_type == "general_user":
        parts.append(_ROLE_GENERAL)

    if patient:
        meds = patient.get("current_medications") or []
        conditions = patient.get("chronic_conditions") or []
        allergies = patient.get("allergies") or []
        dob = patient.get("date_of_birth", "N/A")
        gender = patient.get("gender", "N/A")
        notes = patient.get("notes", "")

        patient_block = f"""
ACTIVE PATIENT PROFILE:
Name: {patient.get("name", "Unknown")} | DOB: {dob} | Gender: {gender}
Chronic Conditions: {", ".join(conditions) if conditions else "None"}
Current Medications: {", ".join(meds) if meds else "None"}
Known Allergies: {", ".join(allergies) if allergies else "None"}"""
        if notes:
            patient_block += f"\nClinical Notes: {notes}"
        patient_block += """

IMPORTANT: Consider this patient's profile when answering every question.
Proactively flag any conflicts between the patient's known allergies and any drug mentioned.
Proactively flag any conflicts between the patient's current medications and any new drug discussed.
When asked to analyse this patient's medications, use the analyze_patient_medications tool."""
        parts.append(patient_block)

    return "\n".join(parts)


def create_medical_agent(
    do_ai_model: str = settings.do_ai_model,
    model_access_key: str = settings.model_access_key,
    temperature: float = 0.3,
    retriever: Optional[VectorStoreRetriever] = None,
    vector_store_manager=None,
):
    """
    Create a MedicaLLM agent using LangGraph's create_react_agent with
    Digital Ocean AI.

    The system prompt is NOT baked in here; it is injected dynamically as the
    first message in every invocation so that patient context and role-specific
    language can be varied per request (O10).
    """
    if retriever:
        set_retriever(retriever)

    if vector_store_manager:
        set_vector_store_manager(vector_store_manager)

    model = ChatOpenAI(
        model=do_ai_model,
        api_key=model_access_key,
        base_url="https://inference.do-ai.run/v1",
        temperature=temperature,
        max_tokens=2048,
        streaming=True,  # Enable streaming for token-by-token output
    )

    agent = create_react_agent(
        model=model,
        tools=ALL_TOOLS,
    )

    pm.suc(f"MedicaLLM Agent created with Digital Ocean AI model: {do_ai_model}")
    return agent

async def init_medical_agent(app):
    """Initialize the medical agent and store it in app.state."""
    
    try:
        pm.inf("Initializing Medical Agent...")
        
        vsm = app.state.vsm
        retriever = app.state.retriever
        
        # Provide PDFProcessor to tools for full-text PDF indexing (O6)
        pdf_processor = await asyncio.get_event_loop().run_in_executor(None, PDFProcessor)
        set_pdf_processor(pdf_processor)

        app.state.medical_agent = create_medical_agent(
            do_ai_model=settings.do_ai_model,
            model_access_key=settings.model_access_key,
            temperature=0.3,
            retriever=retriever,
            vector_store_manager=vsm,
        )
        pm.suc("Medical Agent initialized successfully")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize Medical Agent")
        app.state.medical_agent = None
        pm.war("App will start without agent functionality")
