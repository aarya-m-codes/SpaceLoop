from backend.modules.search.pipeline import SearchPipeline
class DiscoveryService:
    @staticmethod
    def discover(query=None, filters=None):
        return SearchPipeline().search(query=query, filters=filters)
