# encoding: utf-8
"""Exceptions Module"""

from requests.exceptions import HTTPError


class MaximumLengthExceeded(BaseException):
    ...


class NonOkHttpStatusCode(HTTPError):
    ...


class RequiredParameterNotFound(BaseException):
    ...


class UnexpectedEmptyValue(BaseException):
    ...


class UnsupportedType(BaseException):
    ...
