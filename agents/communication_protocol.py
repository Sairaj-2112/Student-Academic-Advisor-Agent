
from models.agent_message import AgentMessage


def send_agent_message(
    sender,
    receiver,
    task,
    message="",
    data=None,
    requires_human_review=False
):
    """
    Creates a structured message between two agents.
    """

    agent_message = AgentMessage(
        sender=sender,
        receiver=receiver,
        task=task,
        status="completed",
        message=message,
        data=data or {},
        requires_human_review=requires_human_review
    )

    print("\n========== AGENT COMMUNICATION ==========")
    print(f"From: {agent_message.sender}")
    print(f"To: {agent_message.receiver}")
    print(f"Task: {agent_message.task}")
    print(f"Status: {agent_message.status}")
    print(f"Message: {agent_message.message}")

    return agent_message.model_dump()
