
from library import DomainError


class TransitionNotAllowed(DomainError):
    def __init__(self, state: str, event: str):
        self.state = state
        self.event = event

        super().__init__(
            f"Событие {event} недопустимо в состоянии «{state}»"
        )


class LoanState:
    name = ""

    @property
    def allowed_events(self):
        """Список событий, допустимых в текущем состоянии."""
        events = (
            "issue_book",
            "debt_found",
            "booking_timeout",
            "extend",
            "due_date_expired",
            "return_book",
            "overdue_30_days",
        )

        return [
            event
            for event in events
            if event in type(self).__dict__
        ]

    def issue_book(self, loan):
        raise TransitionNotAllowed(self.name, "issue_book")

    def debt_found(self, loan):
        raise TransitionNotAllowed(self.name, "debt_found")

    def booking_timeout(self, loan):
        raise TransitionNotAllowed(self.name, "booking_timeout")

    def extend(self, loan):
        raise TransitionNotAllowed(self.name, "extend")

    def due_date_expired(self, loan):
        raise TransitionNotAllowed(self.name, "due_date_expired")

    def return_book(self, loan):
        raise TransitionNotAllowed(self.name, "return_book")

    def overdue_30_days(self, loan):
        raise TransitionNotAllowed(self.name, "overdue_30_days")


class ReservedState(LoanState):
    name = "Забронирована"

    def issue_book(self, loan):
        return IssuedState()

    def debt_found(self, loan):
        return RejectedState()

    def booking_timeout(self, loan):
        return ReservationRemovedState()


class IssuedState(LoanState):
    name = "Выдана"

    def extend(self, loan):
        return ExtendedState()

    def due_date_expired(self, loan):
        return OverdueState()

    def return_book(self, loan):
        return ReturnedState()


class ExtendedState(LoanState):
    name = "Продлена"

    def due_date_expired(self, loan):
        return OverdueState()

    def return_book(self, loan):
        return ReturnedState()


class OverdueState(LoanState):
    name = "Просрочена"

    def return_book(self, loan):
        return ReturnedState()

    def overdue_30_days(self, loan):
        return SentToAdministrationState()


class ReturnedState(LoanState):
    name = "Возвращена"


class RejectedState(LoanState):
    name = "Отклонена"


class ReservationRemovedState(LoanState):
    name = "Бронь снята"


class SentToAdministrationState(LoanState):
    name = "Передана администрации"
