from discord.app_commands import AppCommandError


class WeakError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.context = kwargs
        super().__init__(message)


class CheckError(AppCommandError):
    def __init__(self, message):
        self.message = message
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
class UnexpectedError(Exception): pass
class WrongChannel(CheckError): pass
class UnverifiedUser(CheckError): pass


async def setup(bot): pass
async def teardown(bot): pass
