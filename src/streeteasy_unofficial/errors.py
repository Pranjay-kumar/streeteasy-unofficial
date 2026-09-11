class StreetEasyError(RuntimeError):
    """Base error for the public SDK."""


class TransportError(StreetEasyError):
    pass


class AccessChallengeError(TransportError):
    pass


class VerificationTimeoutError(AccessChallengeError):
    pass


class SchemaChangedError(StreetEasyError):
    pass


class ListingNotFoundError(StreetEasyError):
    pass
