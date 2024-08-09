from datetime import datetime
from collections import deque
import inspect


class Logger:

    logs: deque

    def __init__(self):
        self.logs = deque()

    def log(self, message: str):
        now = datetime.now()
        caller = inspect.currentframe().f_back

        log = f"{now.hour}:{now.minute}:{now.second} - {caller}: {message}"
        self.logs.appendleft(log)
        print(log)
