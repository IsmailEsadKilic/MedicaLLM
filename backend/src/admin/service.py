"""Admin service — aggregate stats for all users."""

import json
from ..db.sql_client import get_session
from ..db.sql_models import User, ConversationRecord, PatientRecord
from .. import printmeup as pm


def get_all_users_stats() -> list[dict]:
    """Get all users with their usage statistics."""
    session = get_session()
    try:
        users = session.query(User).all()
        result = []

        for user in users:
            # Count conversations
            convs = session.query(ConversationRecord).filter(
                ConversationRecord.user_id == user.user_id
            ).all()

            total_messages = 0
            user_messages = 0
            assistant_messages = 0
            tools_used: dict[str, int] = {}

            for conv in convs:
                messages = json.loads(conv.messages) if conv.messages else []
                total_messages += len(messages)
                for msg in messages:
                    if msg.get("role") == "user":
                        user_messages += 1
                    elif msg.get("role") == "assistant":
                        assistant_messages += 1
                    tool = msg.get("tool_used")
                    if tool:
                        tools_used[tool] = tools_used.get(tool, 0) + 1

            # Count patients (for healthcare professionals)
            patient_count = session.query(PatientRecord).filter(
                PatientRecord.healthcare_professional_id == user.user_id
            ).count()

            result.append({
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "account_type": user.account_type,
                "created_at": user.created_at,
                "stats": {
                    "total_conversations": len(convs),
                    "total_messages": total_messages,
                    "user_messages": user_messages,
                    "assistant_messages": assistant_messages,
                    "tools_used": tools_used,
                    "total_tool_calls": sum(tools_used.values()),
                    "patient_count": patient_count,
                },
            })

        # Sort by total messages descending
        result.sort(key=lambda u: u["stats"]["total_messages"], reverse=True)
        return result
    except Exception as e:
        pm.err(e=e, m="Error fetching admin stats")
        return []
    finally:
        session.close()


def get_system_stats() -> dict:
    """Get overall system statistics."""
    session = get_session()
    try:
        from ..db.sql_models import Drug, DrugInteraction, PubmedCache

        total_users = session.query(User).count()
        total_conversations = session.query(ConversationRecord).count()
        total_patients = session.query(PatientRecord).count()
        total_drugs = session.query(Drug).count()
        total_interactions = session.query(DrugInteraction).count()
        total_pubmed_cached = session.query(PubmedCache).count()

        # Count total messages across all conversations
        all_convs = session.query(ConversationRecord).all()
        total_messages = 0
        total_tool_calls = 0
        tool_breakdown: dict[str, int] = {}
        for conv in all_convs:
            messages = json.loads(conv.messages) if conv.messages else []
            total_messages += len(messages)
            for msg in messages:
                tool = msg.get("tool_used")
                if tool:
                    total_tool_calls += 1
                    tool_breakdown[tool] = tool_breakdown.get(tool, 0) + 1

        return {
            "users": total_users,
            "conversations": total_conversations,
            "messages": total_messages,
            "patients": total_patients,
            "drugs_in_database": total_drugs,
            "drug_interactions": total_interactions,
            "pubmed_queries_cached": total_pubmed_cached,
            "total_tool_calls": total_tool_calls,
            "tool_breakdown": tool_breakdown,
        }
    except Exception as e:
        pm.err(e=e, m="Error fetching system stats")
        return {}
    finally:
        session.close()
