class WeakError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.context = kwargs
        super().__init__(message)


class UnableToUpdateDatabase(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class UnableToDecodeJson(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class ErrorFetchingData(WeakError): pass
class ProfileDoesntExist(WeakError): pass
class UsernameAlreadyExists(WeakError): pass
class UsernameDoesNotExist(WeakError): pass
class ScenarioDoesNotExist(WeakError): pass
class UnexpectedError(Exception): pass
