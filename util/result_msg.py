from __future__ import annotations
from enum import Enum


class Result(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ResultMSG:
    """
    Class holding a result [SUCCESS or FAILURE] and optionally a failure message.
    Used for functions that can fail in specific ways and need to return custom error strings.
    """

    def __init__(self, result: Result, message: str = ""):
        self.result = result
        self.message = message

    @staticmethod
    def success() -> ResultMSG:
        """
        Creates a ResultMSG with Result.SUCCESS.
        """

        return ResultMSG(Result.SUCCESS)

    @staticmethod
    def failure(message: str) -> ResultMSG:
        """
        Creates a ResultMSG with Result.FAILURE and the given error message.
        """

        return ResultMSG(Result.FAILURE, message=message)

    def is_success(self):
        return self.result == Result.SUCCESS

    def is_failure(self):
        return self.result == Result.FAILURE

    def __str__(self):
        if self.is_success():
            return f"Result: {self.result.value}"
        else:
            return f"Result: {self.result.value}, Message: {self.message}"
