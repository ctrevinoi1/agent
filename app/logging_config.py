import logging
from logging import StreamHandler
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }
    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL
        record.levelname = f"{color}{record.levelname}{reset}"
        record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)

logger = logging.getLogger("osint")
logger.setLevel(logging.DEBUG)
handler = StreamHandler()
formatter = ColorFormatter('[%(asctime)s] %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler) 