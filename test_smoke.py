import os
def test_app_launches(driver):
    assert driver.current_package == os.environ.get("APP_PACKAGE", "com.example.app")


def test_dump_page_source(driver):
    print(driver.page_source)
