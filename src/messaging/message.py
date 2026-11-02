"""
Estructura de mensajes estandarizados para la arquitectura multiagente (SMA).
Inspirado en el estándar FIPA-ACL (Agent Communication Language).
"""
import time
from typing import Any


class AgentMessage:
    """Mensaje estandarizado entre agentes del sistema SATA-UNSA."""
    def __init__(
        self,
        sender: str,
        receiver: str,
        performative: str,
        content: dict[str, Any],
        conversation_id: str | None = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.performative = performative  # REQUEST, INFORM, QUERY, FAILURE, AGREE
        self.content = content
        self.conversation_id = conversation_id or f"conv_{int(time.time() * 1000)}"
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "performative": self.performative,
            "content": self.content,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp
        }

    def __repr__(self) -> str:
        return f"<AgentMessage {self.performative} from={self.sender} to={self.receiver} conv={self.conversation_id}>"
