from fastapi import APIRouter, HTTPException

from .. import printmeup as pm
from . import service

router = APIRouter(prefix="/api/drug-search", tags=["drug-search"])


@router.get("/search/{query}")
async def endpoint_search_drugs(query: str):
    """Search drugs by name or synonym."""
    try:
        result = service.search_drugs(query)
        return result
    except Exception as e:
        pm.err(e=e, m=f"Search error for '{query}'")
        raise HTTPException(status_code=500, detail="Failed to search drugs")


@router.get("/{drug_name}")
async def endpoint_get_drug_info(drug_name: str):
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
async def endpoint_check_interaction(drug1: str, drug2: str):
    """Check if two drugs have a known interaction."""
    try:
        result = service.check_drug_interaction(drug1, drug2)
        return result
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        raise HTTPException(status_code=500, detail="Failed to check interaction")
