
from pydantic import BaseModel, Field
from typing import Any, Literal


class AgentMessage(BaseModel):
    """
    Standard communication format between AI agents.
    """

    sender: str
    receiver: str
    task: str

    status: Literal[
        "pending",
        "in_progress",
        "completed",
        "failed"
    ] = "pending"

    message: str = ""

    data: dict[str, Any] = Field(default_factory=dict)

    requires_human_review: bool = False
