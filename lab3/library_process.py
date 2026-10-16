from datetime import date, datetime

from library import (
    Book,
    BookId,
    Loan,
    ReaderId,
    DomainInvariantViolation,
    LibraryService,
    InMemoryBookRepository,
    InMemoryLoanRepository,
    
)

from library_events import (
    ReturnReminderSent,
    AdministrationNotified,
)
from library_states import TransitionNotAllowed

class LendingProcess:
    def __init__(
        self,
        books: InMemoryBookRepository,
        loans: InMemoryLoanRepository,
        library_service: LibraryService
    ):
        self._books = books
        self._loans = loans
        self._library_service = library_service
        self._queues = {}
        self._events = []

    def reader_has_debt(self, reader_id: ReaderId) -> bool:
        reader_loans = self._loans.find_by_reader(reader_id)

        return any(
            loan.fine.amount > 0
            for loan in reader_loans
        )

    def review_application(self, loan_id: int):
        loan = self._loans.get(loan_id)

        if self.reader_has_debt(loan.reader_id):
            loan.debt_found()
            self._loans.save(loan)
            return loan

        return self.issue_book(loan_id)

    def was_extended(self, loan: Loan) -> bool:
        return loan.state == "Продлена"

    def book_has_queue(self, book_id: BookId) -> bool:
        return bool(self._queues.get(book_id))

    def extend_loan(self, loan_id: int):
        loan = self._loans.get(loan_id)

        if self.was_extended(loan):
            raise TransitionNotAllowed(loan.state, "extend")

        if self.book_has_queue(loan.book_id):
            raise DomainInvariantViolation(
                "Продление невозможно: на книгу есть очередь"
            )

        loan.extend()
        self._loans.save(loan)

        return loan

    def on_due_date_expired(self, loan_id: int, now: datetime):
        loan = self._loans.get(loan_id)

        if now.date() <= loan.period.due_date:
            raise DomainInvariantViolation(
                "Срок возврата ещё не истёк"
            )

        loan.due_date_expired()
        self._loans.save(loan)

        return loan

    def on_overdue_day(
        self,
        loan_id: int,
        now: datetime,
        fine_per_day: int
    ):
        loan = self._loans.get(loan_id)

        if loan.state != "Просрочена":
            raise DomainInvariantViolation(
                "Штраф начисляется только для просроченной выдачи"
            )

        loan.update_overdue_fine(
            now.date(),
            fine_per_day
        )

        self._loans.save(loan)

        return loan

    def on_overdue_30_days(
        self,
        loan_id: int,
        now: datetime
    ):
        loan = self._loans.get(loan_id)

        if loan.state != "Просрочена":
            raise DomainInvariantViolation(
                "Передача администрации возможна только для просроченной выдачи"
            )

        overdue_days = (
            now.date() - loan.period.due_date
        ).days

        if overdue_days < 30:
            raise DomainInvariantViolation(
                "30 дней просрочки ещё не прошло"
            )

        loan.overdue_30_days()

        event = AdministrationNotified(
            loan_id=loan_id,
            sent_at=now
        )

        self._events.append(event)
        self._loans.save(loan)

        return loan

    def return_book(
        self,
        loan_id: int,
        return_date: date,
        fine_per_day: int
    ):
        loan = self._loans.get(loan_id)
        book = self._books.get(loan.book_id)

        self._library_service.return_book(
            book,
            loan,
            return_date,
            fine_per_day
        )

        loan.return_book()

        self._books.save(book)
        self._loans.save(loan)

        return loan

    def issue_book(self, loan_id: int):
        loan = self._loans.get(loan_id)
        book = self._books.get(loan.book_id)

        self._library_service.issue_book(
            book,
            loan
        )

        loan.issue_book()

        self._books.save(book)
        self._loans.save(loan)

        return loan

    def on_return_reminder(
        self,
        loan_id: int,
        now: datetime
    ):
        loan = self._loans.get(loan_id)

        if loan.state not in ("Выдана", "Продлена"):
            raise DomainInvariantViolation(
                "Напоминание возможно только для действующей выдачи"
            )

        event = ReturnReminderSent(
            loan_id=loan_id,
            sent_at=now
        )

        self._events.append(event)

        return event

    