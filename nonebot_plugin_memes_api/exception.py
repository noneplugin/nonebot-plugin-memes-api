class NetworkError(Exception):
    pass


class PlatformUnsupportError(Exception):
    def __init__(self, platform: str):
        self.platform = platform


class MemeGeneratorException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return self.message


class NoSuchMeme(MemeGeneratorException):
    pass


class TextOverLength(MemeGeneratorException):
    pass


class OpenImageFailed(MemeGeneratorException):
    pass


class ParserExit(MemeGeneratorException):
    pass


class ParamsMismatch(MemeGeneratorException):
    pass


class ImageNumberMismatch(ParamsMismatch):
    pass


class TextNumberMismatch(ParamsMismatch):
    pass


class TextOrNameNotEnough(ParamsMismatch):
    pass


class ArgMismatch(ParamsMismatch):
    pass


class ArgParserExit(ArgMismatch):
    pass


class ArgModelMismatch(ArgMismatch):
    pass
