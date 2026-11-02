"""
Clase base para todos los agentes de la arquitectura multiagente SATA-UNSA.
Define el ciclo de vida y la interfaz de comunicación con el MessageBus.
"""
from abc import ABC, abstractmethod
from typing import Any

from ..messaging.bus import MessageBus
from ..messaging.message import AgentMessage


class BaseAgent(ABC):
    """Agente base autónomo con buzón de mensajes."""
    def __init__(self, agent_id: str, bus: MessageBus):
        self.agent_id = agent_id
        self.bus = bus
        self.bus.register_agent(agent_id)

    def send(self, receiver: str, performative: str, content: dict[str, Any], conversation_id: str | None = None):
        """Envía un mensaje a otro agente a través del bus."""
        msg = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            performative=performative,
            content=content,
            conversation_id=conversation_id
        )
        self.bus.send(msg)

    def receive(self, block: bool = True, timeout: float | None = None) -> AgentMessage | None:
        """Recibe el siguiente mensaje de su buzón."""
        return self.bus.receive(self.agent_id, block=block, timeout=timeout)

    @abstractmethod
    def handle_message(self, message: AgentMessage) -> AgentMessage | None:
        """Procesa un mensaje entrante y genera una respuesta si corresponde."""
