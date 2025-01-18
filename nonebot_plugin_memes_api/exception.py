class NetworkError(Exception):
    pass


class MemeGeneratorException(Exception):
    message: str

    def __str__(self):
        return self.message


class ImageDecodeError(MemeGeneratorException):
    error: str


class ImageEncodeError(MemeGeneratorException):
    error: str


class ImageAssetMissing(MemeGeneratorException):
    path: str


class DeserializeError(MemeGeneratorException):
    error: str


class ImageNumberMismatch(MemeGeneratorException):
    min: int
    max: int
    actual: int


class TextNumberMismatch(MemeGeneratorException):
    min: int
    max: int
    actual: int


class TextOverLength(MemeGeneratorException):
    text: str


class MemeFeedback(MemeGeneratorException):
    feedback: str
