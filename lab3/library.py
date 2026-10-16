
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol


# Доменные исключения

class DomainError(Exception):
    pass


class InvalidValueObject(DomainError):
    pass


class DomainInvariantViolation(DomainError):
    pass


class EntityNotFound(DomainError):
    pass


# Неизменяемое доменное событие

@dataclass(frozen=True)
class LoanEvent:
    event: str
    state: str


# Объекты-значения

@dataclass(frozen=True)
class BookId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject(
                "ID книги должен быть положительным"
            )


@dataclass(frozen=True)
class ReaderId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject(
                "ID читателя должен быть положительным"
            )


@dataclass(frozen=True)
class LoanPeriod:
    issue_date: date
    due_date: date

    def __post_init__(self):
        if self.due_date < self.issue_date:
            raise InvalidValueObject(
                "Срок возврата не может быть раньше даты выдачи"
            )


@dataclass(frozen=True)
class Fine:
    amount: int

    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObject(
                "Сумма штрафа не может быть отрицательной"
            )


# Агрегат Book

class Book:
    def __init__(self, book_id: BookId, total_copies: int):
        if total_copies <= 0:
            raise DomainInvariantViolation(
                "Количество экземпляров должно быть положительным"
            )

        self._id = book_id
        self._total_copies = total_copies
        self._available_copies = total_copies

    @property
    def id(self):
        return self._id

    @property
    def total_copies(self):
        return self._total_copies

    @property
    def available_copies(self):
        return self._available_copies

    def checkout(self):
        if self._available_copies <= 0:
            raise DomainInvariantViolation(
                "Нет свободных экземпляров книги"
            )

        self._available_copies -= 1

    def return_copy(self):
        if self._available_copies >= self._total_copies:
            raise DomainInvariantViolation(
                "Все экземпляры книги уже возвращены"
            )

        self._available_copies += 1


# Агрегат Loan

class Loan:
    def __init__(
        self,
        loan_id: int,
        book_id: BookId,
        reader_id: ReaderId,
        period: LoanPeriod
    ):
        if loan_id <= 0:
            raise InvalidValueObject(
                "ID выдачи должен быть положительным"
            )

        self._id = loan_id
        self._book_id = book_id
        self._reader_id = reader_id
        self._period = period
        self._return_date = None
        self._fine = Fine(0)
        self._events = []

        from library_states import ReservedState
        self._state = ReservedState()

    @property
    def id(self):
        return self._id

    @property
    def book_id(self):
        return self._book_id

    @property
    def reader_id(self):
        return self._reader_id

    @property
    def return_date(self):
        return self._return_date

    @property
    def fine(self):
        return self._fine

    @property
    def state(self):
        return self._state.name

    @property
    def period(self):
        return self._period

    @property
    def events(self):
        return tuple(self._events)

    @property
    def allowed_events(self):
        return list(self._state.allowed_events)

    def _record_event(self, event_name: str):
        self._events.append(
            LoanEvent(
                event=event_name,
                state=self.state
            )
        )

    def issue_book(self):
        self._state = self._state.issue_book(self)
        self._record_event("issue_book")

    def debt_found(self):
        self._state = self._state.debt_found(self)
        self._record_event("debt_found")

    def booking_timeout(self):
        self._state = self._state.booking_timeout(self)
        self._record_event("booking_timeout")

    def extend(self):
        next_state = self._state.extend(self)

        self._period = LoanPeriod(
            self._period.issue_date,
            self._period.due_date + timedelta(days=7)
        )

        self._state = next_state
        self._record_event("extend")

    def due_date_expired(self):
        self._state = self._state.due_date_expired(self)
        self._record_event("due_date_expired")

    def return_book(self):
        self._state = self._state.return_book(self)
        self._record_event("return_book")

    def overdue_30_days(self):
        self._state = self._state.overdue_30_days(self)
        self._record_event("overdue_30_days")

    def update_overdue_fine(self, as_of: date, fine_per_day: int):
        if fine_per_day < 0:
            raise InvalidValueObject(
                "Штраф за день не может быть отрицательным"
            )

        if as_of <= self._period.due_date:
            raise DomainInvariantViolation(
                "Срок возврата ещё не истёк"
            )

        days_late = (as_of - self._period.due_date).days
        self._fine = Fine(days_late * fine_per_day)

        return self._fine

    def close(self, return_date: date, fine_per_day: int):
        if self._return_date is not None:
            raise DomainInvariantViolation(
                "Выдача уже закрыта"
            )

        if return_date < self._period.issue_date:
            raise DomainInvariantViolation(
                "Дата возврата не может быть раньше даты выдачи"
            )

        if fine_per_day < 0:
            raise InvalidValueObject(
                "Штраф за день не может быть отрицательным"
            )

        self._return_date = return_date

        if return_date > self._period.due_date:
            days_late = (
                return_date - self._period.due_date
            ).days

            self._fine = Fine(
                days_late * fine_per_day
            )


# Порт репозитория

class LoanRepository(Protocol):
    def get(self, loan_id: int) -> Loan:
        ...

    def save(self, loan: Loan) -> None:
        ...


# Доменный сервис

class LibraryService:
    def issue_book(
        self,
        book: Book,
        loan: Loan
    ) -> Loan:
        book.checkout()
        return loan

    def return_book(
        self,
        book: Book,
        loan: Loan,
        return_date: date,
        fine_per_day: int
    ) -> Loan:
        loan.close(return_date, fine_per_day)
        book.return_copy()
        return loan


# Репозитории в памяти

class InMemoryBookRepository:
    def __init__(self):
        self._data = {}

    def get(self, book_id: BookId) -> Book:
        if book_id.value not in self._data:
            raise EntityNotFound(
                "Книга не найдена"
            )

        return self._data[book_id.value]

    def save(self, book: Book) -> None:
        self._data[book.id.value] = book


class InMemoryLoanRepository:
    def __init__(self):
        self._data = {}

    def get(self, loan_id: int) -> Loan:
        if loan_id not in self._data:
            raise EntityNotFound(
                "Выдача не найдена"
            )

        return self._data[loan_id]

    def save(self, loan: Loan) -> None:
        self._data[loan.id] = loan

    def find_by_reader(self, reader_id: ReaderId):
        return [
            loan
            for loan in self._data.values()
            if loan.reader_id == reader_id
        ]
