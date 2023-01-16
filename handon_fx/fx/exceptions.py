class NotEnoughCash(Exception):
    """Raised when trying to open a trade with insufficient cash."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)
