class ElasticIpHealthCheckProxy:
    """Placeholder external health-check proxy abstraction."""

    def checkHealth(self, proxyResourceDict: dict) -> dict:
        """Return normalized health-check data once external behavior is implemented."""
        raise NotImplementedError("Elastic IP health checking is not implemented yet.")
