from typing import Annotated, Optional
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_aws import ChatBedrock

from ..drugs import service as drug_service
from ..pubmed import service as pubmed_service
from .. import printmeup as pm
from ..config import settings


# ============================================================
# RAG Retriever State
# ============================================================

_retriever: Optional[VectorStoreRetriever] = None
_vector_store_manager = None
_last_search_sources = None
_last_tool_debug: Optional[dict] = None


def set_retriever(retriever: VectorStoreRetriever):
    global _retriever
    _retriever = retriever
    pm.suc("Retriever set for medical document search")


def set_vector_store_manager(vsm):
    """Set the VectorStoreManager instance for indexing PubMed abstracts."""
    global _vector_store_manager
    _vector_store_manager = vsm
    pm.suc("VectorStoreManager set for PubMed indexing")


def get_retriever() -> Optional[VectorStoreRetriever]:
    return _retriever


def get_last_search_sources():
    global _last_search_sources
    sources = _last_search_sources
    _last_search_sources = None
    return sources


def get_last_tool_debug() -> Optional[dict]:
    """Get and clear debug info from the last tool invocation."""
    global _last_tool_debug
    debug = _last_tool_debug
    _last_tool_debug = None
    return debug


# ============================================================
# TOOL 1: Drug Information Lookup
# ============================================================

@tool
def get_drug_info(
    drug_name: Annotated[str, "Name of the drug (e.g., Warfarin, Metformin, Aspirin)"],
) -> str:
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
        pm.inf(f"Looking up drug: {drug_name}")
        result = drug_service.get_drug_info(drug_name)

        if not result.get("success"):
            return f"Drug not found: {drug_name}"

        parts = []
        drug_name_display = result["drug_name"]
        if result.get("is_synonym"):
            parts.append(f"{result['queried_name']} (also known as {result['actual_name']})")
        else:
            parts.append(drug_name_display)

        for field, label in [
            ("indication", "Indication"),
            ("mechanism_of_action", "Mechanism"),
            ("toxicity", "Side effects/toxicity"),
            ("metabolism", "Metabolism"),
            ("half_life", "Half-life"),
        ]:
            val = result.get(field, "N/A")
            if val != "N/A":
                parts.append(f"{label}: {val}")

        return " | ".join(parts)
    except Exception as e:
        pm.err(e=e, m=f"Error in get_drug_info for '{drug_name}'")
        return f"Error retrieving drug information: {str(e)}"


# ============================================================
# TOOL 2: Drug Interaction Check
# ============================================================

@tool
def check_drug_interaction(
    drug1: Annotated[str, "First drug name"],
    drug2: Annotated[str, "Second drug name"],
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
        pm.inf(f"check_drug_interaction: drug1='{drug1}', drug2='{drug2}'")
        result = drug_service.check_drug_interaction(drug1, drug2)

        if not result.get("success"):
            return f"Error checking interaction: {result.get('error', 'Unknown error')}"

        if result.get("interaction_found"):
            return (
                f"Yes, {result['drug1']} and {result['drug2']} do interact. "
                f"{result['description']} It's important to consult with a healthcare "
                f"provider before taking these medications together."
            )
        else:
            return (
                f"No documented interaction found between {result['drug1']} and "
                f"{result['drug2']}. However, always inform your healthcare provider "
                f"about all medications you're taking."
            )
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        return f"Error checking interaction: {str(e)}"


# ============================================================
# TOOL 3: Drug-Food Interaction Check
# ============================================================

@tool
def check_drug_food_interaction(
    drug_name: Annotated[str, "Name of the drug"],
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
    """
    try:
        pm.inf(f"Checking food interactions for: {drug_name}")
        result = drug_service.get_drug_food_interactions(drug_name)

        if not result.get("success"):
            return f"Error checking food interactions: {result.get('error', 'Unknown error')}"

        if result.get("count", 0) > 0:
            interactions = result["interactions"]
            response = [f"Food Interactions for {result['drug_name']}:", f"Found {result['count']} food interaction(s):\n"]
            for i, interaction in enumerate(interactions, 1):
                response.append(f"{i}. {interaction}")
            response.append("\nAlways follow your healthcare provider's instructions regarding food and medication timing.")
            return "\n".join(response)
        else:
            return (
                f"No specific food interactions are documented for {result['drug_name']} "
                f"in our database. This doesn't mean there are no interactions. Always "
                f"consult your healthcare provider or pharmacist about dietary considerations."
            )
    except Exception as e:
        pm.err(e=e, m=f"Error checking food interactions for '{drug_name}'")
        return f"Error checking food interactions: {str(e)}"


# ============================================================
# TOOL 4: Search Drugs by Category/Indication
# ============================================================

@tool
def search_drugs_by_indication(
    condition: Annotated[str, "Medical condition or therapeutic category (e.g., diabetes, hypertension, pain)"],
) -> str:
    """
    Search for drugs that treat a specific condition or belong to a therapeutic category.

    Use this when the user asks about:
    - What drugs treat a condition
    - Alternative medications for a condition
    - Drug recommendations for a specific disease

    Examples:
    - "What drugs treat diabetes?"
    - "Recommend alternatives for hypertension"
    - "What medications are available for pain?"
    """
    try:
        pm.inf(f"Searching drugs for condition: {condition}")
        result = drug_service.search_drugs_by_category(condition, limit=10)

        if not result.get("success"):
            return f"Error searching drugs: {result.get('error', 'Unknown error')}"

        if result.get("count", 0) == 0:
            return f"No drugs found for '{condition}'. Try different keywords like 'diabetes', 'hypertension', or 'pain'."

        drugs = result["drugs"]
        response = [f"Found {result['count']} drug(s) for {condition}:\n"]
        for i, drug in enumerate(drugs, 1):
            response.append(f"{i}. {drug['name']}")
            if drug.get("categories"):
                response.append(f"   Categories: {', '.join(drug['categories'])}")
            if drug.get("indication") and drug["indication"] != "N/A":
                indication = drug["indication"][:150]
                if len(drug["indication"]) > 150:
                    indication += "..."
                response.append(f"   Indication: {indication}")
            response.append("")

        response.append("Consult your healthcare provider before starting any medication.")
        return "\n".join(response)
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs for '{condition}'")
        return f"Error searching drugs: {str(e)}"


# ============================================================
# TOOL 5: Medical Document Search (RAG)
# ============================================================

@tool
def search_medical_documents(
    query: Annotated[str, "Medical question or topic to search for"],
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
        return "Medical document search is currently unavailable. I can still help with drug information and interactions."

    try:
        pm.inf(f"Searching medical documents for: {query}")
        docs = retriever.invoke(query)

        if not docs:
            _last_search_sources = None
            return "No relevant medical documents found for your query."

        _last_search_sources = [
            {
                "source": doc.metadata.get("source", doc.metadata.get("file_name", "Unknown")),
                "page": doc.metadata.get("page", ""),
                "content": doc.page_content[:200],
            }
            for doc in docs[:3]
        ]

        context = "\n\n".join([doc.page_content for doc in docs])

        llm = ChatBedrock(
            model=settings.bedrock_llm_id,
            model_kwargs={"temperature": 0.3, "max_tokens": 2048},
        )

        prompt = (
            f"Based on the following medical information, answer this question: {query}\n\n"
            f"Medical Information:\n{context}\n\n"
            f"Provide a comprehensive, accurate answer based solely on the information provided above. "
            f"If the information doesn't contain a clear answer, say so."
        )

        response = llm.invoke(prompt)
        answer = response.content if isinstance(response.content, str) else str(response.content)

        response_parts = [answer, "\n\nSources:"]
        seen_sources = set()
        for i, doc in enumerate(docs[:3], 1):
            source_name = doc.metadata.get("source", doc.metadata.get("file_name", "Unknown"))
            page = doc.metadata.get("page", "")
            source_key = f"{source_name}_{page}"
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)

            if page:
                response_parts.append(f"{i}. {source_name} (Page {page})")
            else:
                response_parts.append(f"{i}. {source_name}")

            snippet = doc.page_content[:150].strip()
            if len(doc.page_content) > 150:
                snippet += "..."
            response_parts.append(f'   "{snippet}"')

        return "\n".join(response_parts)
    except Exception as e:
        pm.err(e=e, m=f"Error searching documents for '{query}'")
        return f"Error searching documents: {str(e)}"


# ============================================================
# TOOL 6: PubMed Literature Search
# ============================================================

@tool
def search_pubmed(
    query: Annotated[str, "Medical research query to search PubMed for"],
) -> str:
    """
    Search PubMed for published medical research articles and clinical studies.

    Use this when the user asks about:
    - Recent medical research or clinical studies
    - Evidence-based medicine or scientific evidence
    - Published papers on a medical topic
    - "What does the research say about..."
    - Literature review or scientific findings
    - Clinical trials or study results

    Examples:
    - "What research exists on metformin and longevity?"
    - "Find studies about SGLT2 inhibitors in heart failure"
    - "What does the literature say about statin side effects?"
    - "Recent research on mRNA vaccines"
    """
    global _last_search_sources, _last_tool_debug

    debug_info = {
        "cache_hit": False,
        "articles_fetched": 0,
        "articles_indexed": 0,
        "already_indexed": 0,
    }

    try:
        pm.inf(f"PubMed search for: {query}")

        # Step 1: Check DynamoDB cache
        articles = pubmed_service.get_cached_results(query)
        if articles is not None:
            debug_info["cache_hit"] = True
            debug_info["articles_fetched"] = len(articles)
            pm.inf(f"Using cached PubMed results ({len(articles)} articles)")
        else:
            # Step 2: Live search via pymed
            articles = pubmed_service.search_pubmed(query)
            debug_info["articles_fetched"] = len(articles)

            if not articles:
                _last_search_sources = None
                _last_tool_debug = debug_info
                return "No PubMed articles found for your query. Try different or broader search terms."

            # Step 3: Cache results in DynamoDB
            pubmed_service.cache_results(query, articles)

        # Step 4: Index new abstracts into ChromaDB (skip already-indexed)
        if _vector_store_manager:
            new_chunks = []
            for article in articles:
                pmid = article.get("pmid", "")
                abstract = article.get("abstract", "")
                title = article.get("title", "")

                if not pmid or not abstract:
                    continue

                if pubmed_service.is_pmid_indexed(pmid):
                    debug_info["already_indexed"] += 1
                    continue

                # Create a LangChain Document for the abstract
                doc = Document(
                    page_content=f"{title}\n\n{abstract}",
                    metadata={
                        "source": "PubMed",
                        "pmid": pmid,
                        "title": title,
                        "journal": article.get("journal", ""),
                        "doi": article.get("doi", ""),
                    },
                )
                new_chunks.append((pmid, title, doc))

            if new_chunks:
                docs_to_add = [chunk[2] for chunk in new_chunks]
                if _vector_store_manager.add_documents(docs_to_add):
                    for pmid, title, _ in new_chunks:
                        pubmed_service.mark_pmid_indexed(pmid, title)
                    debug_info["articles_indexed"] = len(new_chunks)
                    pm.suc(f"Indexed {len(new_chunks)} new PubMed abstracts into ChromaDB")
        else:
            pm.war("VectorStoreManager not available, skipping ChromaDB indexing")

        # Step 5: Build context and summarize with LLM (same pattern as search_medical_documents)
        context_parts = []
        for article in articles:
            title = article.get("title", "Untitled")
            abstract = article.get("abstract", "No abstract available.")
            journal = article.get("journal", "")
            date = article.get("publication_date", "")
            context_parts.append(f"Title: {title}\nJournal: {journal} ({date})\n\n{abstract}")

        context = "\n\n---\n\n".join(context_parts)

        llm = ChatBedrock(
            model=settings.bedrock_llm_id,
            model_kwargs={"temperature": 0.3, "max_tokens": 2048},
        )

        prompt = (
            f"Based on the following PubMed research articles, answer this question: {query}\n\n"
            f"Research Articles:\n{context}\n\n"
            f"Provide a comprehensive, evidence-based answer. Cite the articles by their title when relevant. "
            f"If the articles don't contain a clear answer, say so."
        )

        response = llm.invoke(prompt)
        answer = response.content if isinstance(response.content, str) else str(response.content)

        # Build sources for session tracking
        _last_search_sources = []
        response_parts = [answer, "\n\nPubMed Sources:"]
        for i, article in enumerate(articles, 1):
            title = article.get("title", "Untitled")
            journal = article.get("journal", "")
            pmid = article.get("pmid", "")
            doi = article.get("doi", "")

            source_line = f"{i}. {title}"
            if journal:
                source_line += f" — {journal}"
            if pmid:
                source_line += f" (PMID: {pmid})"
            response_parts.append(source_line)

            if doi:
                response_parts.append(f"   DOI: https://doi.org/{doi}")

            _last_search_sources.append({
                "source": f"PubMed — {journal}" if journal else "PubMed",
                "pmid": pmid,
                "title": title,
                "content": (article.get("abstract", ""))[:200],
            })

        _last_tool_debug = debug_info
        return "\n".join(response_parts)

    except Exception as e:
        pm.err(e=e, m=f"Error searching PubMed for '{query}'")
        _last_tool_debug = debug_info
        return f"Error searching PubMed: {str(e)}"


# ============================================================
# All tools list for agent creation
# ============================================================

ALL_TOOLS = [
    get_drug_info,
    check_drug_interaction,
    check_drug_food_interaction,
    search_drugs_by_indication,
    search_medical_documents,
    search_pubmed,
]
