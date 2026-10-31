import os
import time
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

from utils.step_logger import StepLogger
from utils.device_logs import clear_logcat, save_logcat
from utils import media

APPIUM_SERVER = "http://localhost:4723"
DEVICE_NAME = os.environ.get("ANDROID_SERIAL", "emulator-5554")
APP_PACKAGE = os.environ.get("APP_PACKAGE", "com.example.app")
APP_ACTIVITY = os.environ.get("APP_ACTIVITY", ".MainActivity")

REPORTS_ROOT = Path(__file__).parent / "reports"


@pytest.fixture(scope="function")
def run_dir():
    d = REPORTS_ROOT / time.strftime("%Y%m%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="function")
def step_logger(run_dir):
    logger = StepLogger(run_dir / "steps.log")
    yield logger
    logger.close()


@pytest.fixture
def driver(run_dir):
    clear_logcat(DEVICE_NAME)

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = DEVICE_NAME
    options.udid = DEVICE_NAME
    options.app_package = APP_PACKAGE
    options.app_activity = APP_ACTIVITY
    options.no_reset = True
    options.new_command_timeout = 300

    drv = webdriver.Remote(APPIUM_SERVER, options=options)

    try:
        media.start_recording(drv)
    except Exception:
        pass

    yield drv

    try:
        video_path = run_dir / "session_recording.mp4"
        media.stop_recording(drv, video_path)
    except Exception:
        pass

    save_logcat(DEVICE_NAME, run_dir / "logcat_full.txt", APP_PACKAGE)

    try:
        drv.quit()
    except Exception:
        pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        run_dir = item.funcargs.get("run_dir")
        drv = item.funcargs.get("driver")
        if run_dir and drv:
            try:
                shot_path = run_dir / f"FAILURE_{item.name}.png"
                media.screenshot(drv, shot_path)
            except Exception:
                pass
            try:
                save_logcat(DEVICE_NAME, run_dir / f"FAILURE_{item.name}_logcat.txt", APP_PACKAGE)
            except Exception:
                pass
