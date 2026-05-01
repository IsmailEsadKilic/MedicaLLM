from typing import Literal
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from ..users.models import PatientDetails
from ..config import settings
from .tools import ALL_TOOLS

#aig
SYSTEM_PROMPT = """\
    You are MedicaLLM, an evidence-based medical information assistant for healthcare professionals.

    # ZERO-HALLUCINATION POLICY:
    - Every clinical claim MUST cite a [REF] number from retrieved PubMed sources.
    - NEVER add facts, statistics, guidelines, drug dosages, risk numbers, or recommendations from your training data.
    - If sources don't cover something, say: "The retrieved literature does not address this."

    CONVERSATIONAL: For greetings and casual chat, respond warmly without tools.

    MULTI-TOOL: Chain tools when needed (drug info → interactions → PubMed → alternatives).

    PUBMED RESPONSE FORMAT — MANDATORY:
    When search_pubmed results are available, your response MUST have EXACTLY 3 sections:

    # Short Answer
    (2-3 sentences with [REF] citations)

    # Evidence Summary
    (What sources found. EVERY sentence needs a [REF]. Use tables for multiple studies. Each table row on its own line.)

    # Limitations
    (What sources do NOT cover: "The retrieved literature does not address...")

    # FORBIDDEN in PubMed responses:
    - Sections like "Clinical Recommendations", "Practical Guidance", "Decision Framework", "Alternative Therapies"
    - Drug dosages, screening protocols, treatment algorithms not in sources
    - Statistics or risk numbers not explicitly in the abstracts
    - Any sentence without [REF] (except Limitations section)

    # TOOLS (use silently):
    1. get_drug_info — drug information
    2. check_drug_interaction — drug interactions
    3. check_drug_food_interaction — drug-food interactions
    4. search_drugs_by_indication — drugs by condition
    5. search_pubmed — PubMed research (convert query to English MeSH terms, default 5 articles)
    6. recommend_alternative_drug — safe alternatives
    7. analyze_patient_medications — patient medication safety analysis

    # INTERACTION RESPONSES:
    Direct answer → What happens → Why it matters → Action needed → call recommend_alternative_drug.

    # TABLE FORMAT:
    Each row on a SEPARATE line. Never put entire table on one line.

    # FINAL RULE:
    #When PubMed sources are available, your ENTIRE response must be grounded in those sources. Uncited clinical claims are FORBIDDEN."""
#aig
_ROLE_HEALTHCARE = """\
    RESPONSE LANGUAGE — HEALTHCARE PROFESSIONAL:
    You are speaking with a qualified healthcare professional. Use precise clinical terminology.
    Include mechanism of action, pharmacokinetic considerations (absorption, distribution, metabolism,
    excretion), evidence-based citations, and dosing guidance where relevant. Assume the reader has
    medical training and does not need lay explanations for standard clinical concepts."""
#aig
_ROLE_GENERAL = """\
    RESPONSE LANGUAGE — GENERAL USER:
    You are speaking with a member of the general public. Use plain, accessible language.
    Avoid medical jargon; when technical terms are unavoidable, explain them in parentheses.
    Focus on practical safety advice and always recommend consulting a licensed healthcare provider
    before making any medication decisions."""


def build_system_prompt(
    is_doctor: bool = False,
    patient: PatientDetails | None = None,
) -> str:
    parts = [SYSTEM_PROMPT]
    if is_doctor:
        parts.append(_ROLE_HEALTHCARE)
    else:
        parts.append(_ROLE_GENERAL)
    if patient:
        meds = patient.current_medications
        conditions = patient.chronic_conditions
        allergies = patient.allergies
        dob = patient.date_of_birth
        gender = patient.gender
        notes = patient.notes
        patient_block = f"""\
            ACTIVE PATIENT PROFILE:
            Name: {patient.name} | DOB: {dob} | Gender: {gender}
            Chronic Conditions: {", ".join(conditions) if conditions else "None"}
            Current Medications: {", ".join(meds) if meds else "None"}
            Known Allergies: {", ".join(allergies) if allergies else "None"}"""
        if notes:
            patient_block += f"\nClinical Notes: {notes}"
        patient_block += """\
            IMPORTANT: Consider this patient's profile when answering every question.
            Proactively flag any conflicts between the patient's known allergies and any drug mentioned.
            Proactively flag any conflicts between the patient's current medications and any new drug discussed.
            When asked to analyse this patient's medications, use the analyze_patient_medications tool."""
        parts.append(patient_block)

    return "\n".join(parts)


def create_medical_agent(
    llm_model_id: str = settings.llm_model_id,
    temperature: float = settings.llm_temperature,
    max_iterations: int = settings.llm_max_iterations,
):
    model = ChatOpenAI(
        model=llm_model_id,
        api_key=SecretStr(settings.llm_api_key),
        base_url=settings.llm_base_url,
        temperature=temperature,
        max_completion_tokens=settings.llm_max_tokens,
        streaming=settings.llm_streaming,
    )
    agent = create_agent(
        model=model,
        tools=ALL_TOOLS,
    )
    return agent
