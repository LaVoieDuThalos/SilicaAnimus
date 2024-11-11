from typing import Callable
import asyncio


class Event:
    def __init__(self):
        self.subscribers: set[Callable] = set()

    def subscribe(self, function):
        self.subscribers.add(function)

    async def __call__(self, *args, **kwargs):
        async with asyncio.TaskGroup() as tg:
            for subscriber in self.subscribers:
                tg.create_task(subscriber(*args, **kwargs))
