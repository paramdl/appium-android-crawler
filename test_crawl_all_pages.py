import os
from crawler import Crawler
from utils.reporter import write_crawl_summary

DEVICE_NAME = os.environ.get("ANDROID_SERIAL", "emulator-5554")
APP_PACKAGE = os.environ.get("APP_PACKAGE", "com.example.app")


def test_crawl_all_pages(driver, run_dir, step_logger):
    crawler = Crawler(
        driver=driver,
        serial=DEVICE_NAME,
        app_package=APP_PACKAGE,
        run_dir=run_dir,
        step_logger=step_logger,
        max_pages=30,
        max_taps=150,
        max_depth=6,
    )
    crawler.crawl()

    summary_path = write_crawl_summary(run_dir, crawler.pages, crawler.issues, crawler.edges)
    step_logger.step(f"Crawl complete: {len(crawler.pages)} pages, {len(crawler.issues)} issues")
    step_logger.step(f"Summary written to {summary_path}")

    assert len(crawler.issues) == 0, f"{len(crawler.issues)} issue(s) found during crawl — see {summary_path}"
