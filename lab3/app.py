
import logging
from datetime import date, datetime

from flask import Flask, jsonify, request

from clock import SystemClock, ClockTimeReversal
from library import (
    Book,
    BookId,
    Loan,
    ReaderId,
    LoanPeriod,
    DomainError,
    DomainInvariantViolation,
    InvalidValueObject,
    EntityNotFound,
    LibraryService,
    InMemoryBookRepository,
    InMemoryLoanRepository,
)
from library_states import TransitionNotAllowed
from library_process import LendingProcess


logger = logging.getLogger(__name__)


class GatewayUnresolved(Exception):
    """Ошибка, при которой внешний шлюз не смог разрешить операцию."""
    pass


def create_app():
    app = Flask(__name__)

    # Все зависимости создаются один раз при запуске приложения.
    clock = SystemClock()
    books = InMemoryBookRepository()
    loans = InMemoryLoanRepository()
    library_service = LibraryService()

    process = LendingProcess(
        books,
        loans,
        library_service
    )

    app.config["clock"] = clock
    app.config["books"] = books
    app.config["loans"] = loans
    app.config["process"] = process

    def loan_to_dict(loan):
        return {
            "id": loan.id,
            "book_id": loan.book_id.value,
            "reader_id": loan.reader_id.value,
            "state": loan.state,
            "issue_date": loan.period.issue_date.isoformat(),
            "due_date": loan.period.due_date.isoformat(),
            "return_date": (
                loan.return_date.isoformat()
                if loan.return_date
                else None
            ),
            "fine": loan.fine.amount,
            "allowed_events": loan.allowed_events,
            "events": [
                {
                    "event": event.event,
                    "state": event.state,
                }
                for event in loan.events
            ],
        }

    def error_response(code, message, status):
        return jsonify({
            "error": code,
            "message": str(message),
        }), status

    # Общая обработка ошибок.

    @app.errorhandler(TransitionNotAllowed)
    def handle_transition_error(error):
        return error_response(
            "transition_not_allowed",
            error,
            409
        )

    @app.errorhandler(EntityNotFound)
    def handle_not_found(error):
        return error_response(
            "entity_not_found",
            error,
            404
        )

    @app.errorhandler(InvalidValueObject)
    def handle_invalid_value(error):
        return error_response(
            "validation_error",
            error,
            422
        )

    @app.errorhandler(DomainInvariantViolation)
    def handle_invariant_violation(error):
        return error_response(
            "invariant_violation",
            error,
            422
        )

    @app.errorhandler(ClockTimeReversal)
    def handle_clock_reversal(error):
        return error_response(
            "clock_time_reversal",
            error,
            422
        )

    @app.errorhandler(GatewayUnresolved)
    def handle_gateway_error(error):
        return error_response(
            "gateway_unresolved",
            error,
            500
        )

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return error_response(
            "validation_error",
            "Некорректное значение: проверьте формат даты и числовых полей",
            422
        )

    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return error_response(
            "domain_error",
            error,
            422
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Необработанная ошибка API")
        return error_response(
            "internal_error",
            "Внутренняя ошибка сервера",
            500
        )

    # Получение состояния выдачи.

    @app.get("/loans/<int:loan_id>")
    def get_loan(loan_id):
        loan = loans.get(loan_id)
        return jsonify(loan_to_dict(loan)), 200

    # Создание выдачи.

    @app.post("/loans")
    def create_loan():
        data = request.get_json(silent=True) or {}

        required_fields = (
            "loan_id",
            "book_id",
            "reader_id",
            "issue_date",
            "due_date",
            "total_copies",
        )

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            return error_response(
                "validation_error",
                "Не переданы обязательные поля: "
                + ", ".join(missing),
                422
            )

        issue_date = date.fromisoformat(data["issue_date"])
        due_date = date.fromisoformat(data["due_date"])

        book_id = BookId(int(data["book_id"]))
        reader_id = ReaderId(int(data["reader_id"]))

        book = Book(
            book_id,
            int(data["total_copies"])
        )

        loan = Loan(
            int(data["loan_id"]),
            book_id,
            reader_id,
            LoanPeriod(issue_date, due_date)
        )

        books.save(book)
        loans.save(loan)

        return jsonify(loan_to_dict(loan)), 201

    # Рассмотрение заявки.

    @app.post("/loans/<int:loan_id>/review")
    def review_loan(loan_id):
        loan = process.review_application(loan_id)
        return jsonify(loan_to_dict(loan)), 200

    # Выдача книги.

    @app.post("/loans/<int:loan_id>/issue")
    def issue_loan(loan_id):
        loan = process.issue_book(loan_id)
        return jsonify(loan_to_dict(loan)), 200

    # Истечение срока бронирования.

    @app.post("/loans/<int:loan_id>/booking-timeout")
    def booking_timeout(loan_id):
        loan = loans.get(loan_id)
        loan.booking_timeout()
        loans.save(loan)

        return jsonify(loan_to_dict(loan)), 200

    # Продление срока выдачи.

    @app.post("/loans/<int:loan_id>/extend")
    def extend_loan(loan_id):
        loan = process.extend_loan(loan_id)
        return jsonify(loan_to_dict(loan)), 200

    # Возврат книги.

    @app.post("/loans/<int:loan_id>/return")
    def return_loan(loan_id):
        data = request.get_json(silent=True) or {}

        return_date = (
            date.fromisoformat(data["return_date"])
            if data.get("return_date")
            else clock.now().date()
        )

        fine_per_day = int(data.get("fine_per_day", 10))

        loan = process.return_book(
            loan_id,
            return_date,
            fine_per_day
        )

        return jsonify(loan_to_dict(loan)), 200

    # Отправка напоминания.

    @app.post("/loans/<int:loan_id>/reminder")
    def send_reminder(loan_id):
        event = process.on_return_reminder(
            loan_id,
            clock.now()
        )

        return jsonify({
            "loan_id": event.loan_id,
            "sent_at": event.sent_at.isoformat(),
        }), 200

    # Наступление срока возврата.

    @app.post("/loans/<int:loan_id>/overdue")
    def mark_overdue(loan_id):
        loan = process.on_due_date_expired(
            loan_id,
            clock.now()
        )

        return jsonify(loan_to_dict(loan)), 200

    # Начисление штрафа.

    @app.post("/loans/<int:loan_id>/fine")
    def update_fine(loan_id):
        data = request.get_json(silent=True) or {}

        fine_per_day = int(data.get("fine_per_day", 10))

        loan = process.on_overdue_day(
            loan_id,
            clock.now(),
            fine_per_day
        )

        return jsonify(loan_to_dict(loan)), 200

    # Передача дела администрации после 30 дней просрочки.

    @app.post("/loans/<int:loan_id>/administration")
    def send_to_administration(loan_id):
        loan = process.on_overdue_30_days(
            loan_id,
            clock.now()
        )

        return jsonify(loan_to_dict(loan)), 200

    # Служебное управление временем приложения.

    @app.post("/internal/tick")
    def tick():
        data = request.get_json(silent=True) or {}

        if "now" in data and data["now"] is not None:
            if not isinstance(data["now"], str):
                return error_response(
                    "validation_error",
                    "Поле now должно быть строкой с датой и временем ISO 8601",
                    422
                )

            try:
                target_time = datetime.fromisoformat(data["now"])
            except ValueError:
                return error_response(
                    "validation_error",
                    "Поле now должно содержать дату и время в формате ISO 8601",
                    422
                )

            now = clock.set_time(target_time)
        else:
            now = clock.now()

        # Вызываем временные события только для тех выдач,
        # которым соответствующее событие разрешено.
        for loan in list(loans._data.values()):
            if (
                "due_date_expired" in loan.allowed_events
                and now.date() > loan.period.due_date
            ):
                process.on_due_date_expired(loan.id, now)

            loan = loans.get(loan.id)

            if (
                "overdue_30_days" in loan.allowed_events
                and (now.date() - loan.period.due_date).days >= 30
            ):
                process.on_overdue_30_days(loan.id, now)

        return jsonify({
            "message": "Время приложения обновлено",
            "now": now.isoformat(),
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)