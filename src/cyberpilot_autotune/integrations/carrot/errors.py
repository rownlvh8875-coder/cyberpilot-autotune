"""Stable typed errors contain no raw reader or external exception text."""


class CarrotDependencyUnavailable(ImportError):
    def __init__(self) -> None:
        super().__init__("CARROT_DEPENDENCY_UNAVAILABLE")


class CarrotSchemaIncompatible(RuntimeError):
    def __init__(self) -> None:
        super().__init__("CARROT_SCHEMA_INCOMPATIBLE")


class CarrotInputError(ValueError):
    """A structurally invalid sample/configuration supplied by the caller."""


class CarrotSessionRequired(CarrotInputError):
    def __init__(self) -> None:
        super().__init__("NEW_SESSION_REQUIRED")
