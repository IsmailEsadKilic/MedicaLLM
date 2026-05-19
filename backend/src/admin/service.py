"""Admin service — provides system stats and user listing for the admin panel."""
import json
from logging import getLogger

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ..db.sql_client import get_session
from ..db.sql_models import (
    ConversationRecord,
    DoctorPatientAssociation,
    DoctorRecord,
    PatientRecord,
    UserRecord,
)

logger = getLogger(__name__)


def _parse_messages_stats(raw_messages: str | None) -> tuple[int, int, int, dict]:
    """Parse a conversation's messages JSON and return (user_msgs, assistant_msgs, tool_calls, tools_used)."""
    try:
        msgs = json.loads(raw_messages) if raw_messages else []
    except (json.JSONDecodeError, TypeError):
        return 0, 0, 0, {}
    user_msgs = 0
    assistant_msgs = 0
    tool_calls = 0
    tools: dict[str, int] = {}
    for msg in msgs:
        role = msg.get("role", "")
        if role == "user":
            user_msgs += 1
        elif role == "assistant":
            assistant_msgs += 1
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc.get("name", tc.get("function", {}).get("name", "unknown"))
                tools[name] = tools.get(name, 0) + 1
                tool_calls += 1
        elif role == "tool":
            name = msg.get("name", "unknown")
            tools[name] = tools.get(name, 0) + 1
            tool_calls += 1
    return user_msgs, assistant_msgs, tool_calls, tools


def get_system_stats() -> dict:
    """Aggregate system-wide statistics for the admin dashboard."""
    session = get_session()
    try:
        total_users = session.query(func.count(UserRecord.id)).scalar() or 0
        total_conversations = session.query(func.count(ConversationRecord.id)).scalar() or 0
        total_patients = session.query(func.count(PatientRecord.id)).scalar() or 0

        from ..db.sql_models import Drug, DrugInteraction
        drugs_count = session.query(func.count(Drug.id)).scalar() or 0
        interactions_count = session.query(func.count(DrugInteraction.id)).scalar() or 0

        # Parse messages from the most recent 200 conversations only (performance)
        recent_convos = (
            session.query(ConversationRecord.messages)
            .order_by(ConversationRecord.id.desc())
            .limit(200)
            .all()
        )
        total_messages = 0
        total_tool_calls = 0
        tool_breakdown: dict[str, int] = {}

        for (raw_messages,) in recent_convos:
            u, a, tc, tools = _parse_messages_stats(raw_messages)
            total_messages += u + a
            total_tool_calls += tc
            for name, count in tools.items():
                tool_breakdown[name] = tool_breakdown.get(name, 0) + count

        return {
            "users": total_users,
            "conversations": total_conversations,
            "messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "patients": total_patients,
            "drugs_in_database": drugs_count,
            "drug_interactions": interactions_count,
            "pubmed_articles_indexed": 0,
            "tool_breakdown": tool_breakdown,
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}", exc_info=True)
        return {
            "users": 0, "conversations": 0, "messages": 0,
            "total_tool_calls": 0, "patients": 0,
            "drugs_in_database": 0, "drug_interactions": 0,
            "pubmed_articles_indexed": 0, "tool_breakdown": {},
        }
    finally:
        session.close()


def get_all_users() -> list[dict]:
    """Return all users with their stats for the admin panel."""
    session = get_session()
    try:
        # Load users with their profiles in one query (avoid N+1)
        users = (
            session.query(UserRecord)
            .options(joinedload(UserRecord.doctor_profile), joinedload(UserRecord.patient_profile))
            .all()
        )

        # Get conversation counts per user in one query
        convo_counts = dict(
            session.query(ConversationRecord.user_pk, func.count(ConversationRecord.id))
            .group_by(ConversationRecord.user_pk)
            .all()
        )

        # Get patient counts for doctors in one query
        doctor_patient_counts: dict[int, int] = {}
        for row in users:
            if row.doctor_profile:
                doctor_patient_counts[row.doctor_profile.id] = 0
        if doctor_patient_counts:
            counts = (
                session.query(DoctorPatientAssociation.doctor_pk, func.count(DoctorPatientAssociation.id))
                .filter(DoctorPatientAssociation.doctor_pk.in_(doctor_patient_counts.keys()))
                .group_by(DoctorPatientAssociation.doctor_pk)
                .all()
            )
            for doc_pk, cnt in counts:
                doctor_patient_counts[doc_pk] = cnt

        # Load last 5 conversations per user for message stats (limit expensive parsing)
        all_user_pks = [u.id for u in users]
        recent_convos_by_user: dict[int, list] = {pk: [] for pk in all_user_pks}
        if all_user_pks:
            # Get IDs of latest 5 conversations per user using a subquery approach
            from sqlalchemy import and_
            convos = (
                session.query(ConversationRecord.user_pk, ConversationRecord.messages)
                .filter(ConversationRecord.user_pk.in_(all_user_pks))
                .order_by(ConversationRecord.id.desc())
                .all()
            )
            for user_pk, messages in convos:
                if len(recent_convos_by_user[user_pk]) < 10:
                    recent_convos_by_user[user_pk].append(messages)

        result = []
        for user in users:
            account_type = "user"
            if user.doctor_profile:
                account_type = "doctor"
            elif user.patient_profile:
                account_type = "patient"

            total_conversations = convo_counts.get(user.id, 0)
            patient_count = doctor_patient_counts.get(user.doctor_profile.id, 0) if user.doctor_profile else 0

            # Parse message stats from recent conversations only
            user_messages = 0
            assistant_messages = 0
            total_tool_calls = 0
            tools_used: dict[str, int] = {}
            for raw_msg in recent_convos_by_user.get(user.id, []):
                u, a, tc, tools = _parse_messages_stats(raw_msg)
                user_messages += u
                assistant_messages += a
                total_tool_calls += tc
                for name, count in tools.items():
                    tools_used[name] = tools_used.get(name, 0) + count

            result.append({
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "account_type": account_type,
                "created_at": user.created_at,
                "stats": {
                    "total_conversations": total_conversations,
                    "total_messages": user_messages + assistant_messages,
                    "user_messages": user_messages,
                    "assistant_messages": assistant_messages,
                    "total_tool_calls": total_tool_calls,
                    "patient_count": patient_count,
                    "tools_used": tools_used,
                },
            })

        return result
    except Exception as e:
        logger.error(f"Error getting all users: {e}", exc_info=True)
        return []
    finally:
        session.close()


def get_all_doctors() -> list[dict]:
    """Return all doctors for admin management."""
    session = get_session()
    try:
        doctors = session.query(DoctorRecord).all()
        result = []
        for doc in doctors:
            user = session.query(UserRecord).filter(UserRecord.id == doc.user_pk).first()
            patient_count = session.query(func.count(DoctorPatientAssociation.id)).filter(
                DoctorPatientAssociation.doctor_pk == doc.id
            ).scalar() or 0
            result.append({
                "doctor_id": doc.doctor_id,
                "name": user.name if user else "Unknown",
                "email": user.email if user else "",
                "specialty": doc.specialty or "",
                "patient_count": patient_count,
            })
        return result
    except Exception as e:
        logger.error(f"Error getting doctors: {e}", exc_info=True)
        return []
    finally:
        session.close()


def get_all_patients() -> list[dict]:
    """Return all patients for admin management."""
    session = get_session()
    try:
        patients = session.query(PatientRecord).all()
        result = []
        for pat in patients:
            user = session.query(UserRecord).filter(UserRecord.id == pat.user_pk).first()
            doctor_count = session.query(func.count(DoctorPatientAssociation.id)).filter(
                DoctorPatientAssociation.patient_pk == pat.id
            ).scalar() or 0
            result.append({
                "patient_id": pat.patient_id,
                "name": user.name if user else "Unknown",
                "email": user.email if user else "",
                "doctor_count": doctor_count,
            })
        return result
    except Exception as e:
        logger.error(f"Error getting patients: {e}", exc_info=True)
        return []
    finally:
        session.close()


def get_all_relationships() -> list[dict]:
    """Return all doctor-patient assignments."""
    session = get_session()
    try:
        assocs = session.query(DoctorPatientAssociation).all()
        result = []
        for assoc in assocs:
            doctor = assoc.doctor
            patient = assoc.patient
            doc_user = session.query(UserRecord).filter(UserRecord.id == doctor.user_pk).first() if doctor else None
            pat_user = session.query(UserRecord).filter(UserRecord.id == patient.user_pk).first() if patient else None
            result.append({
                "doctor_id": doctor.doctor_id if doctor else "",
                "doctor_name": doc_user.name if doc_user else "Unknown",
                "patient_id": patient.patient_id if patient else "",
                "patient_name": pat_user.name if pat_user else "Unknown",
                "created_at": assoc.created_at or "",
            })
        return result
    except Exception as e:
        logger.error(f"Error getting relationships: {e}", exc_info=True)
        return []
    finally:
        session.close()
