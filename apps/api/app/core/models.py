"""Immutable, provider-neutral values exchanged across QH boundaries.

These types define data shape only. Validation, authorization, persistence and
conversation behavior are deliberately deferred to later tickets.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NewType

ContextId = NewType("ContextId", str)
SubjectId = NewType("SubjectId", str)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRecord:
    id: ContextId
    content: str
    title: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextQuery:
    text: str
    limit: int = 20


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextResult:
    contexts: tuple[ContextRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRequest:
    subject_id: SubjectId
    query: ContextQuery


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True, kw_only=True)
class Message:
    role: MessageRole
    content: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationRequest:
    messages: tuple[Message, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationResult:
    message: Message
