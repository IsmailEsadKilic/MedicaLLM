"""
Quick test script to verify agent tools work correctly.
Run with: python -m backend.test_agent_tools
"""

import asyncio
from backend.src.agent.tools import (
    get_drug_info,
    check_drug_interactions,
    check_drug_food_interaction,
    search_drugs_by_indication,
    search_drugs_by_category,
    recommend_alternative_drug,
    set_current_patient_id,
)


async def test_get_drug_info():
    print("\n" + "="*60)
    print("TEST 1: get_drug_info")
    print("="*60)
    
    # Test with different detail levels
    result = get_drug_info.invoke({"drug_name": "Aspirin", "detail": "low"})
    print("\n[LOW DETAIL]")
    print(result)
    
    result = get_drug_info.invoke({"drug_name": "Warfarin", "detail": "moderate"})
    print("\n[MODERATE DETAIL]")
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # Test with synonym
    result = get_drug_info.invoke({"drug_name": "Tylenol", "detail": "low"})
    print("\n[SYNONYM TEST - Tylenol]")
    print(result[:300] + "..." if len(result) > 300 else result)


async def test_check_drug_interactions():
    print("\n" + "="*60)
    print("TEST 2: check_drug_interactions")
    print("="*60)
    
    result = check_drug_interactions.invoke({
        "drug_names": ["Warfarin", "Aspirin", "Ibuprofen"]
    })
    print(result)


async def test_check_drug_food_interaction():
    print("\n" + "="*60)
    print("TEST 3: check_drug_food_interaction")
    print("="*60)
    
    result = check_drug_food_interaction.invoke({
        "drug_name": "Warfarin",
        "food_items": ["grapefruit"]
    })
    print(result)


async def test_search_drugs_by_indication():
    print("\n" + "="*60)
    print("TEST 4: search_drugs_by_indication")
    print("="*60)
    
    result = search_drugs_by_indication.invoke({
        "condition": "hypertension"
    })
    print(result[:500] + "..." if len(result) > 500 else result)


async def test_search_drugs_by_category():
    print("\n" + "="*60)
    print("TEST 5: search_drugs_by_category")
    print("="*60)
    
    result = search_drugs_by_category.invoke({
        "category": "antibiotic"
    })
    print(result[:500] + "..." if len(result) > 500 else result)


async def test_recommend_alternative_drug():
    print("\n" + "="*60)
    print("TEST 6: recommend_alternative_drug")
    print("="*60)
    
    result = recommend_alternative_drug.invoke({
        "current_drug_names": ["Aspirin", "Lisinopril"],
        "for_drug_name": "Warfarin"
    })
    print(result[:500] + "..." if len(result) > 500 else result)


async def main():
    print("\n" + "="*60)
    print("AGENT TOOLS TEST SUITE")
    print("="*60)
    
    try:
        await test_get_drug_info()
        await test_check_drug_interactions()
        await test_check_drug_food_interaction()
        await test_search_drugs_by_indication()
        await test_search_drugs_by_category()
        await test_recommend_alternative_drug()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
