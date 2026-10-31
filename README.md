# Appium Android Crawler

An exploratory crawler for Android apps built on Appium + pytest. It taps through every reachable screen,
fingerprints each page, and files an issue report whenever the app crashes, freezes or leaves the app,
with a screenshot, screen recording and the matching logcat slice.

## What it does
- **Crawls** breadth-first up to configurable limits (pages, taps, depth), fingerprinting screens so it doesn't loop.
- **Detects** crashes (logcat `FATAL EXCEPTION` / ANR), unexpected exits from the app and dead-end screens.
- **Reports** each issue as `issues/<id>/report.md` + `meta.json`, plus a run `SUMMARY.md` with a page map.
- **Captures evidence:** per-page screenshots, a full-session recording and the full logcat.
- **Smoke test** that the target app launches and is in the foreground.

## Run
```bash
pip install -r requirements.txt
appium                                  # Appium 2 with the UiAutomator2 driver
export ANDROID_SERIAL=emulator-5554     # or a device serial / host:port for wireless adb
export APP_PACKAGE=com.example.app
export APP_ACTIVITY=.MainActivity
pytest -q                               # reports land in reports/<timestamp>/
```

## Layout
```
conftest.py               driver, run folder, step logger, logcat + recording fixtures
crawler.py                the crawl loop and issue detection
test_smoke.py             app launches
test_crawl_all_pages.py   full crawl
utils/                    fingerprinting, device logs, media capture, report writer
```
