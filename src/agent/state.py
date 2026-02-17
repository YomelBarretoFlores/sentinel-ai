from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    messages: List[str]
    current_step: str
    current_error: Optional[str]
    affected_service: Optional[str]
    diagnosis_log: List[str]
    candidate_plan: Optional[str]
    approval_status: str
    retry_count: int
    memory_consulted: bool
    security_flags: List[str]
    escalation_reason: Optional[str]
