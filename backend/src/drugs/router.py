from fastapi import APIRouter, HTTPException, Request
from .models import (
    Drug, CheckDrugInteractionRequest,
    CheckDrugInteractionResponse,
    DrugSearchRequest,
    DrugSearchResponse
)

from . import service
from ..middleware.rate_limiter import limiter, SEARCH_LIMIT, user_key

from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/api/drug-search", tags=["drug-search"])

@router.get("/search/{query}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_search_drugs(
    request: Request,
    query: str,
    include_semantic_search: bool = False,
    min_similarity: float = 0.3
    ):
    try:
        drug_search_request = DrugSearchRequest(
            query=query,
            include_semantic_search=include_semantic_search,
            min_similarity=min_similarity
        )
        result: DrugSearchResponse = service.search_drugs(drug_search_request)
        return result
    except Exception as e:
        logger.error(f"Error searching drugs with query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search drugs")


@router.get("/{drug_id}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_get_drug_by_id(request: Request, drug_id: str):
    """
    Get detailed drug information by drug ID.
    
    For fuzzy search by name instead of looking up by ID,
    use the /search endpoint with ?include_semantic_search=true first to find the drug ID,
    then call this endpoint with that ID to get the full drug info.
    """
    try:
        result = service.get_drug(drug_id)
        if not result:
            raise HTTPException(
                status_code=404, detail=f"Drug '{drug_id}' not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching drug info for '{drug_id}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch drug info")


@router.get("/interaction/{drug1_id}/{drug2_id}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_check_pair_interaction_by_ids(request: Request, drug1_id: str, drug2_id: str):
    """
    Check for interactions between two drugs by their ids.
    """
    try:
        drug_interaction_check_request = CheckDrugInteractionRequest(drug_ids=[drug1_id, drug2_id])
        result: CheckDrugInteractionResponse = service.check_drug_interactions(drug_interaction_check_request)
        return result
    except Exception as e:
        logger.error(f"Error checking interaction between '{drug1_id}' and '{drug2_id}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check interaction")
    
@router.get("/interactions")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_check_multiple_interactions_by_id(request: Request, body: CheckDrugInteractionRequest):
    """
    Check for interactions between multiple drug ids.
    """
    try:
        result: CheckDrugInteractionResponse = service.check_drug_interactions(body)
        return result
    except Exception as e:
        logger.error(f"Error checking interactions for drugs '{body.drug_ids}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check interactions")