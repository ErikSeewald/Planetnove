from __future__ import annotations


class RequestResponse:
    _approved: bool
    msg: str

    def __init__(self, is_approved: bool, msg: str):
        self._approved = is_approved
        self.msg = msg

    @staticmethod
    def approve(msg: str) -> RequestResponse:
        return RequestResponse(True, msg)

    @staticmethod
    def deny(msg: str) -> RequestResponse:
        return RequestResponse(False, msg)

    def as_dict(self) -> dict:
        return {
            "is_approved": self.is_approved(),
            "message": self.get_message()
        }

    def is_approved(self):
        return self._approved

    def get_message(self):
        return self.msg
