from datetime import datetime
from collections import deque
import inspect


class Logger:
    """
    Class responsible for all logging by the tank robot.
    """

    logs: deque

    def __init__(self):
        self.logs = deque()

    def log(self, message: str):
        """
        Logs the given message along with additional debug information.
        The log is also saved in a deque.
        """

        now = datetime.now()
        frame = inspect.currentframe().f_back
        caller = frame.f_code.co_name

        log = f"{now.hour}:{now.minute}:{now.second} - {caller} (line {frame.f_lineno}): {message}"
        self.logs.appendleft(log)
        print(log)
