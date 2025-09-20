class Logger:
    def __init__(self, silent_mode=False):
        self.silent_mode = silent_mode

    def log(self, message: str, level: str = "INFO"):
        if not self.silent_mode:
            print(f"[{level}] {message}")
