"""
Bus de mensajería desacoplado para la arquitectura multiagente (costo cero, local).
Gestiona colas de mensajes en memoria y bitácora de trazabilidad.
"""
import queue
import time
from typing import Dict, List, Optional
from .message import AgentMessage


class MessageBus:
    """Bus de mensajería asíncrono/síncrono entre agentes."""
    def __init__(self):
        self._queues: Dict[str, queue.Queue] = {}
        self.history: List[AgentMessage] = []

    def register_agent(self, agent_id: str):
        """Registra un agente y crea su buzón de entrada."""
        if agent_id not in self._queues:
            self._queues[agent_id] = queue.Queue()

    def send(self, message: AgentMessage):
        """Envía un mensaje al buzón del receptor y lo registra en la bitácora."""
        self.history.append(message)
        if message.receiver in self._queues:
            self._queues[message.receiver].put(message)
        else:
            raise ValueError(f"Agente receptor '{message.receiver}' no registrado en el bus.")

    def receive(self, agent_id: str, block: bool = True, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Extrae el siguiente mensaje del buzón del agente."""
        if agent_id not in self._queues:
            return None
        try:
            return self._queues[agent_id].get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def get_history_summary(self) -> List[Dict]:
        """Retorna el historial de mensajes formateado para auditoría y visualización."""
        return [
            {
                "time": time.strftime("%H:%M:%S", time.localtime(m.timestamp)),
                "sender": m.sender,
                "receiver": m.receiver,
                "performative": m.performative,
                "conversation_id": m.conversation_id,
                "summary": str(m.content)[:100] + "..." if len(str(m.content)) > 100 else str(m.content)
            }
            for m in self.history
        ]
