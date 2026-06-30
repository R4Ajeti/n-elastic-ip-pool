class ElasticIpPoolRepo:
    """Placeholder data access abstraction for Elastic IP pool resources."""

    def listResource(self) -> list[dict]:
        """Return stored proxy/IP resources once storage behavior is implemented."""
        raise NotImplementedError("Elastic IP pool listing is not implemented yet.")

    def saveResource(self, resourceDict: dict) -> dict:
        """Save a proxy/IP resource once storage behavior is implemented."""
        raise NotImplementedError("Elastic IP pool saving is not implemented yet.")

    def updateResource(self, resourceIdStr: str, resourceDict: dict) -> dict:
        """Update a proxy/IP resource once storage behavior is implemented."""
        raise NotImplementedError("Elastic IP pool updating is not implemented yet.")
