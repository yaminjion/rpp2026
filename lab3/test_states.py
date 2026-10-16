from datetime import date

from library import (
    BookId,
    ReaderId,
    LoanPeriod,
    Loan
)

from library_states import TransitionNotAllowed


loan = Loan(
    1,
    BookId(1),
    ReaderId(1),
    LoanPeriod(
        date(2026, 10, 15),
        date(2026, 10, 29)
    )
)

print("Начальное состояние:", loan.state)

loan.issue_book()
print("После выдачи:", loan.state)

loan.extend()
print("После продления:", loan.state)


print("\nПроверка недопустимого перехода:")

try:
    loan.issue_book()
except TransitionNotAllowed as error:
    print(error)