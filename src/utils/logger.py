from datetime import datetime, timezone


def _get_current_time():
    timestamp_string = (
        datetime.now(timezone.utc).astimezone().strftime("%d/%b/%Y %H:%M:%S UTC%z")
    )
    timestamp_string = "{0}:{1}".format(timestamp_string[:-2], timestamp_string[-2:])
    return timestamp_string


def info(message):
    current_time = _get_current_time()
    print(f"\033[92m[INFO] {current_time} - {message}\033[00m")


def warn(message):
    current_time = _get_current_time()
    print(f"\033[93m[WARNING] {current_time} - {message}\033[00m")


def error(message):
    current_time = _get_current_time()
    print(f"\033[91m[ERROR] {current_time} - {message}\033[00m")
