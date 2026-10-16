from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReturnReminderSent:
    loan_id: int
    sent_at: datetime


@dataclass(frozen=True)
class AdministrationNotified:
    loan_id: int
    sent_at: datetime