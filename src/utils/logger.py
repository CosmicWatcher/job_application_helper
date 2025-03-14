from datetime import datetime, timezone
import os
from typing import Literal

from config import ROOT_PATH


class ANSIColors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[33m"


def _get_color_code(level: Literal["INFO", "WARN", "ERROR"]):
    match level:
        case "INFO":
            return ANSIColors.GREEN
        case "WARN":
            return ANSIColors.YELLOW
        case "ERROR":
            return ANSIColors.RED


def _get_current_time():
    timestamp_string = (
        datetime.now(timezone.utc).astimezone().strftime("%d/%b/%Y %H:%M:%S UTC%z")
    )
    timestamp_string = "{0}:{1}".format(timestamp_string[:-2], timestamp_string[-2:])
    return timestamp_string


def _print_to_console(level: Literal["INFO", "WARN", "ERROR"], message: str):
    current_time = _get_current_time()
    color_code = _get_color_code(level)

    print(f"{color_code}[{level}]\t{current_time} - {message}{ANSIColors.RESET}")


def _save_to_file(level: Literal["INFO", "WARN", "ERROR"], message: str):
    current_time = _get_current_time()
    color_code = _get_color_code(level)

    log_dir = os.path.join(
        ROOT_PATH,
        "logs",
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    log_entry = f"{color_code}[{level}]\t{current_time} - {message}{ANSIColors.RESET}\n"

    with open(log_file, "a") as f:
        f.write(log_entry)


def info(message: str):
    _print_to_console("INFO", message)
    _save_to_file("INFO", message)


def warn(message: str):
    _print_to_console("WARN", message)
    _save_to_file("WARN", message)


def error(message: str):
    _print_to_console("ERROR", message)
    _save_to_file("ERROR", message)
