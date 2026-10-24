"""
Clase base para todos los agentes de la arquitectura multiagente SATA-UNSA.
Define el ciclo de vida y la interfaz de comunicación con el MessageBus.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..messaging.message import AgentMessage
from ..messaging.bus import MessageBus


class BaseAgent(ABC):
    """Agente base autónomo con buzón de mensajes."""
    def __init__(self, agent_id: str, bus: MessageBus):
        self.agent_id = agent_id
        self.bus = bus
        self.bus.register_agent(agent_id)

    def send(self, receiver: str, performative: str, content: Dict[str, Any], conversation_id: Optional[str] = None):
        """Envía un mensaje a otro agente a través del bus."""
        msg = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            performative=performative,
            content=content,
            conversation_id=conversation_id
        )
        self.bus.send(msg)

    def receive(self, block: bool = True, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Recibe el siguiente mensaje de su buzón."""
        return self.bus.receive(self.agent_id, block=block, timeout=timeout)

    @abstractmethod
    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Procesa un mensaje entrante y genera una respuesta si corresponde."""
        pass
