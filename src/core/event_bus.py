import asyncio
from datetime import datetime
from typing import List, Callable, Awaitable

class EventBus:
    def __init__(self):
        self._queues: List[asyncio.Queue] = []

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._queues.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._queues:
            self._queues.remove(queue)

    def publish(self, event_type: str, message: str, details: dict = None):
        payload = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "details": details or {}
        }

        for queue in list(self._queues):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

bus = EventBus()

def log(event_type: str, message: str, details: dict = None):
    print(f"[{event_type.upper()}] {message}")
    bus.publish(event_type, message, details)
