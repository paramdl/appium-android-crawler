import hashlib
import re
import xml.etree.ElementTree as ET

from appium.webdriver.common.appiumby import AppiumBy

IGNORED_ATTRS = {"bounds", "index"}


def page_fingerprint(driver):
    """Hash of the screen's structural content (class+resource-id+text), ignoring volatile bits."""
    source = driver.page_source
    root = ET.fromstring(source.encode("utf-8"))
    parts = []
    for node in root.iter():
        cls = node.attrib.get("class", "")
        rid = node.attrib.get("resource-id", "")
        text = node.attrib.get("text", "")
        if cls or rid or text:
            parts.append(f"{cls}|{rid}|{text}")
    digest = hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]
    return digest


def page_title_guess(driver, max_len=60):
    """Best-effort human label for a screen: first non-empty text node."""
    source = driver.page_source
    root = ET.fromstring(source.encode("utf-8"))
    for node in root.iter():
        text = node.attrib.get("text", "").strip()
        if text:
            return re.sub(r"\s+", " ", text)[:max_len]
    return "unlabeled screen"


def get_clickable_elements(driver):
    return driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")


def describe_element(el):
    try:
        text = el.get_attribute("text") or el.get_attribute("content-desc") or ""
        rid = el.get_attribute("resource-id") or ""
        cls = el.get_attribute("className") or el.get_attribute("class") or ""
        label = text.strip() or rid.split("/")[-1] or cls
        return label[:60]
    except Exception:
        return "unknown-element"
