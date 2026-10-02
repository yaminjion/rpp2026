class DomainInvariantViolation(Exception):
    """Ошибка нарушения бизнес-правила предметной области."""
    pass


class InvalidValueObject(ValueError):
    """Ошибка создания некорректного объекта-значения."""
    pass