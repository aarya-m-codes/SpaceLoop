class EventBus:
    _subscribers = {}
    @classmethod
    def subscribe(cls, event_name, handler):
        cls._subscribers.setdefault(event_name, []).append(handler)
    @classmethod
    def publish(cls, event):
        for h in cls._subscribers.get(event.name, []):
            h(event)
