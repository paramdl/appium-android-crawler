import subprocess

CRASH_MARKERS = ("FATAL EXCEPTION", "ANR in", "has died", "Process crashed")


def clear_logcat(serial):
    subprocess.run(["adb", "-s", serial, "logcat", "-c"], check=False)


def dump_logcat(serial, app_package=None):
    result = subprocess.run(
        ["adb", "-s", serial, "logcat", "-d"],
        capture_output=True, text=True, errors="ignore", check=False,
    )
    lines = result.stdout.splitlines()
    if app_package:
        lines = [l for l in lines if app_package in l or "FATAL" in l or "AndroidRuntime" in l]
    return "\n".join(lines)


def find_crash(log_text):
    for marker in CRASH_MARKERS:
        idx = log_text.find(marker)
        if idx != -1:
            start = log_text.rfind("\n", 0, idx)
            return log_text[max(0, start - 2000):idx + 3000]
    return None


def save_logcat(serial, path, app_package=None):
    text = dump_logcat(serial, app_package)
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    return text
