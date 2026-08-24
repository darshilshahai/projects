class CricketEngineError(Exception):
    code = "INVALID_DELIVERY"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class InvalidDeliveryError(CricketEngineError):
    code = "INVALID_DELIVERY"


class InvalidExtraCombinationError(InvalidDeliveryError):
    code = "INVALID_EXTRA_COMBINATION"


class InvalidDismissalError(CricketEngineError):
    code = "INVALID_DISMISSAL"


class InvalidWicketForNoBallError(InvalidDismissalError):
    code = "INVALID_WICKET_FOR_NO_BALL"


class InvalidWicketForWideError(InvalidDismissalError):
    code = "INVALID_WICKET_FOR_WIDE"


class InningsStateError(CricketEngineError):
    code = "INNINGS_NOT_LIVE"


class BatterSelectionRequiredError(InningsStateError):
    code = "BATTER_SELECTION_REQUIRED"

    def __init__(self) -> None:
        super().__init__("Select the incoming batter before the next delivery.")


class BowlerSelectionRequiredError(InningsStateError):
    code = "BOWLER_SELECTION_REQUIRED"

    def __init__(self) -> None:
        super().__init__("Select the next bowler before the next delivery.")


class InvalidNextBatterError(CricketEngineError):
    code = "INVALID_NEXT_BATTER"


class InvalidBowlerError(CricketEngineError):
    code = "INVALID_BOWLER"


class InningsCompleteError(InningsStateError):
    code = "INNINGS_COMPLETE"

    def __init__(self) -> None:
        super().__init__("This innings is complete.")


class MatchCompleteError(InningsStateError):
    code = "MATCH_COMPLETE"

    def __init__(self) -> None:
        super().__init__("This match is complete.")
