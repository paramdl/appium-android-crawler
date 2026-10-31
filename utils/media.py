import base64


def screenshot(driver, path):
    driver.get_screenshot_as_file(str(path))
    return path


def start_recording(driver):
    driver.start_recording_screen()


def stop_recording(driver, path):
    b64_video = driver.stop_recording_screen()
    if not b64_video:
        return None
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64_video))
    return path
