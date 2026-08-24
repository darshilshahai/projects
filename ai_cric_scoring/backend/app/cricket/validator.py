from __future__ import annotations

from app.cricket.commands import DeliveryCommand
from app.cricket.exceptions import (
    InvalidDismissalError,
    InvalidExtraCombinationError,
    InvalidWicketForNoBallError,
    InvalidWicketForWideError,
)
from app.cricket.types import (
    NO_BALL_ALLOWED_DISMISSALS,
    WIDE_FORBIDDEN_DISMISSALS,
    DismissalType,
)


def validate_delivery(command: DeliveryCommand) -> None:
    for name, value in (
        ("runs_off_bat", command.runs_off_bat),
        ("wides", command.wides),
        ("no_balls", command.no_balls),
        ("byes", command.byes),
        ("leg_byes", command.leg_byes),
        ("penalty_runs", command.penalty_runs),
    ):
        if value < 0:
            raise InvalidExtraCombinationError(f"{name} cannot be negative.")

    if command.wides > 0 and command.no_balls > 0:
        raise InvalidExtraCombinationError("A delivery cannot be both a wide and a no-ball.")
    if command.byes > 0 and command.leg_byes > 0:
        raise InvalidExtraCombinationError("A delivery cannot include both byes and leg byes.")
    if command.wides > 0 and command.runs_off_bat > 0:
        raise InvalidExtraCombinationError("Runs off the bat cannot be scored from a wide.")
    if command.wides > 0 and (command.byes > 0 or command.leg_byes > 0):
        raise InvalidExtraCombinationError("Byes and leg byes cannot be combined with a wide.")

    dismissal = command.dismissal
    if dismissal is None:
        return
    if command.wides > 0 and dismissal.type in WIDE_FORBIDDEN_DISMISSALS:
        raise InvalidWicketForWideError(f"{dismissal.type} cannot occur from a wide.")
    if command.no_balls > 0 and dismissal.type not in NO_BALL_ALLOWED_DISMISSALS:
        raise InvalidWicketForNoBallError(f"{dismissal.type} cannot occur from a no-ball.")
    if dismissal.type == DismissalType.RETIRED_OUT:
        raise InvalidDismissalError("Use a retirement command for retired out.")
