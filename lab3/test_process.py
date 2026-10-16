from datetime import date, datetime

from library import (
    BookId,
    ReaderId,
    LoanPeriod,
    Book,
    Loan,
    LibraryService,
    InMemoryBookRepository,
    InMemoryLoanRepository,
)

from library_process import LendingProcess


books = InMemoryBookRepository()
loans = InMemoryLoanRepository()

book = Book(
    BookId(1),
    total_copies=2
)

loan = Loan(
    1,
    BookId(1),
    ReaderId(1),
    LoanPeriod(
        date(2026, 10, 1),
        date(2026, 10, 15)
    )
)

books.save(book)
loans.save(loan)

process = LendingProcess(
    books,
    loans,
    LibraryService()
)

print("Начальное состояние:", loan.state)

process.review_application(1)
print("После выдачи:", loan.state)

process.extend_loan(1)
print("После продления:", loan.state)
print("Новый срок возврата:", loan.period.due_date)

process.on_return_reminder(
    1,
    datetime(2026, 10, 20, 12, 0)
)
print("Напоминание сформировано")

process.on_due_date_expired(
    1,
    datetime(2026, 10, 23, 12, 0)
)
print("После истечения срока:", loan.state)

process.on_overdue_day(
    1,
    datetime(2026, 10, 25, 12, 0),
    fine_per_day=100
)
print("Штраф:", loan.fine.amount)

process.return_book(
    1,
    date(2026, 10, 25),
    fine_per_day=100
)
print("После возврата:", loan.state)

