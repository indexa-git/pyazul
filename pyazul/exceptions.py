# encoding: utf-8
"""Exceptions Module"""

from requests.exceptions import HTTPError


class MinimumLengthNotReached(BaseException):
    ...

class NonOkHttpStatusCode(HTTPError):
    ...

class RequiredParameterNotFound(BaseException):
    ...

class UnexpectedEmptyValue(BaseException):
    ...

class UnsuportedType(BaseException):
    ...
