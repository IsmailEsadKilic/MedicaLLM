from typing import Optional
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..config import settings
from .. import printmeup as pm
from .tools import ALL_TOOLS


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are MedicaLLM, an evidence-based medical information assistant for healthcare professionals.

ZERO-HALLUCINATION POLICY:
- Every clinical claim MUST cite a [REF] number from retrieved PubMed sources.
- NEVER add facts, statistics, guidelines, drug dosages, risk numbers, or recommendations from your training data.
- If sources don't cover something, say: "The retrieved literature does not address this."

CONVERSATIONAL: For greetings and casual chat, respond warmly without tools.

MULTI-TOOL: Chain tools when needed (drug info → interactions → PubMed → alternatives).

PUBMED RESPONSE FORMAT — MANDATORY:
When search_pubmed results are available, your response MUST have EXACTLY 3 sections:

## Short Answer
(2-3 sentences with [REF] citations)

## Evidence Summary
(What sources found. EVERY sentence needs a [REF]. Use tables for multiple studies. Each table row on its own line.)

## Limitations
(What sources do NOT cover: "The retrieved literature does not address...")

FORBIDDEN in PubMed responses:
- Sections like "Clinical Recommendations", "Practical Guidance", "Decision Framework", "Alternative Therapies"
- Drug dosages, screening protocols, treatment algorithms not in sources
- Statistics or risk numbers not explicitly in the abstracts
- Any sentence without [REF] (except Limitations section)

TOOLS (use silently):
1. get_drug_info — drug information
2. check_drug_interaction — drug interactions
3. check_drug_food_interaction — drug-food interactions
4. search_drugs_by_indication — drugs by condition
5. search_pubmed — PubMed research (convert query to English MeSH terms, default 5 articles)
6. recommend_alternative_drug — safe alternatives
7. analyze_patient_medications — patient medication safety analysis

INTERACTION RESPONSES: Direct answer → What happens → Why it matters → Action needed → call recommend_alternative_drug.

TABLE FORMAT: Each row on a SEPARATE line. Never put entire table on one line.

FINAL RULE: When PubMed sources are available, your ENTIRE response must be grounded in those sources. Uncited clinical claims are FORBIDDEN."""


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
    temperature: float = 0.0,
    max_iterations: int = 50,  # Maximum reasoning steps for multi-tool chains
):
    """
    Create a MedicaLLM agent using LangGraph's create_react_agent with
    Digital Ocean AI.

    The system prompt is NOT baked in here; it is injected dynamically as the
    first message in every invocation so that patient context and role-specific
    language can be varied per request (O10).
    """

    model = ChatOpenAI(
        model=do_ai_model,
        api_key=model_access_key,
        base_url="https://inference.do-ai.run/v1",
        temperature=temperature,
        max_tokens=2048,  # Limited to prevent verbose hallucination
        streaming=True,  # Enable streaming for token-by-token output
    )

    agent = create_react_agent(
        model=model,
        tools=ALL_TOOLS,
    )

    pm.suc(f"MedicaLLM Agent created with Digital Ocean AI model: {do_ai_model}")
    pm.inf(f"Agent configured with max_iterations={max_iterations} for multi-tool reasoning")
    return agent

async def init_medical_agent(app):
    """Initialize the medical agent and store it in app.state."""
    
    try:
        pm.inf("Initializing Medical Agent...")

        app.state.medical_agent = create_medical_agent(
            do_ai_model=settings.do_ai_model,
            model_access_key=settings.model_access_key,
            temperature=0.0,
        )
        pm.suc("Medical Agent initialized successfully")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize Medical Agent")
        app.state.medical_agent = None
        pm.war("App will start without agent functionality")
