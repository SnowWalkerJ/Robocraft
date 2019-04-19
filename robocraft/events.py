from collections import defaultdict, deque


class EventHandler:
    def __init__(self):
        self.handlers = defaultdict(list)
        self.events = deque()

    def register(self, event, handler):
        self.handlers[event].append(handler)

    def unregister(self, event, handler):
        self.handlers[event].remove(handler)

    def fire(self, event, *args, **kwargs):
        self.events.append((event, args, kwargs))

    async def poll(self):
        while self.events:
            event, args, kwargs = self.events.popleft()
            for handler in self.handlers[event]:
                await handler(*args, **kwargs)
