from fastapi import APIRouter, HTTPException, Request

from . import service
from ..middleware.rate_limiter import limiter, SEARCH_LIMIT, user_key

from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/api/drug-search", tags=["drug-search"])

@router.get("/search/{query}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_search_drugs(request: Request, query: str):
    """Search drugs by name or synonym."""
    try:
        result = service.search_drugs(query)
        return result
    except Exception as e:
        logger.error(f"Error searching drugs with query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search drugs")


@router.get("/{drug_name}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_get_drug_info(request: Request, drug_name: str):
    """Get detailed drug information by name."""
    try:
        result = service.get_drug_info(drug_name)
        if not result.get("success"):
            raise HTTPException(
                status_code=404, detail=f"Drug '{drug_name}' not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error fetching drug info for '{drug_name}'")
        raise HTTPException(status_code=500, detail="Failed to fetch drug info")


@router.get("/interaction/{drug1}/{drug2}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_check_interaction(request: Request, drug1: str, drug2: str):
    """Check if two drugs have a known interaction."""
    try:
        result = service.check_drug_interaction(drug1, drug2)
        return result
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        raise HTTPException(status_code=500, detail="Failed to check interaction")


@router.get("/alternatives/{drug_name}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_get_alternatives(request: Request, drug_name: str, patient_medications: str = ""):
    """
    Get safe alternative drugs for a given drug.
    Optionally pass a comma-separated list of the patient's current medications
    via ?patient_medications=Drug1,Drug2 to filter out alternatives that interact
    with those drugs.
    """
    try:
        med_list = [m.strip() for m in patient_medications.split(",") if m.strip()] if patient_medications else []
        result = service.get_alternative_drugs(drug_name, med_list)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error finding alternatives for '{drug_name}'")
        raise HTTPException(status_code=500, detail="Failed to find alternative drugs")


@router.get("/products/{drug_name}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_get_drug_products(request: Request, drug_name: str):
    """Return brand-name products for a drug."""
    try:
        result = service.get_drug_products(drug_name)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error fetching products for '{drug_name}'")
        raise HTTPException(status_code=500, detail="Failed to fetch products")


@router.get("/references/{drug_name}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_get_drug_references(request: Request, drug_name: str):
    """Return general references (PubMed articles, textbooks, links) for a drug."""
    try:
        result = service.get_drug_references(drug_name)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error fetching references for '{drug_name}'")
        raise HTTPException(status_code=500, detail="Failed to fetch references")


@router.get("/product-lookup/{product_name}")
@limiter.limit(SEARCH_LIMIT, key_func=user_key)
async def endpoint_search_by_product(request: Request, product_name: str):
    """Look up which drug(s) a commercial product name belongs to."""
    try:
        result = service.search_by_product_name(product_name)
        return result
    except Exception as e:
        pm.err(e=e, m=f"Error looking up product '{product_name}'")
        raise HTTPException(status_code=500, detail="Failed to look up product")