from dataclasses import dataclass
from enum import Enum

from app.core.models import ContextId, SubjectId


class PolicyAction(str, Enum):
    CREATE_CONTEXT = "create_context"
    LIST_CONTEXTS = "list_contexts"
    UPDATE_CONTEXT = "update_context"
    DELETE_CONTEXT = "delete_context"
    READ_CONTEXT = "read_context"
    PROJECT_CONTEXT = "project_context"
    CHAT = "chat"
    ORGANIZE_ENVIRONMENT = "organize_environment"
    PROPOSE_UPDATE = "propose_update"
    CONFIRM_UPDATE = "confirm_update"
    READ_SNAPSHOT = "read_snapshot"
    ASK_SNAPSHOT = "ask_snapshot"


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyRequest:
    subject_id: SubjectId | None
    action: PolicyAction
    context_ids: tuple[ContextId, ...] = ()
    snapshot_id: str | None = None
    guest_session_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None
