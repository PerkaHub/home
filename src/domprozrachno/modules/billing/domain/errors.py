class ChargeError(Exception):
    pass


class ChargeNotFound(ChargeError):
    pass


class InvalidCharge(ChargeError):
    pass


class AlreadyPublished(ChargeError):
    pass


class PeriodAlreadyPublished(ChargeError):
    pass
