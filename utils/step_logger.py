import time


class StepLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        self.steps = []
        self._file = open(log_path, "a", encoding="utf-8")

    def step(self, message):
        entry = f"[{time.strftime('%H:%M:%S')}] {message}"
        self.steps.append(entry)
        self._file.write(entry + "\n")
        self._file.flush()
        print(entry)

    def path_so_far(self):
        return list(self.steps)

    def close(self):
        self._file.close()
