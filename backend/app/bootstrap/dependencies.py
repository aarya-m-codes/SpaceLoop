class DependencyContainer:
    _instance = None
    def __init__(self):
        self.services = {}
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DependencyContainer()
        return cls._instance
