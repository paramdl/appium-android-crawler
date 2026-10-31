import time

from utils.fingerprint import page_fingerprint, page_title_guess, get_clickable_elements, describe_element
from utils.device_logs import dump_logcat, find_crash
from utils.reporter import write_issue_report
from utils import media


class Crawler:
    def __init__(self, driver, serial, app_package, run_dir, step_logger,
                 max_pages=40, max_taps=200, max_depth=6, settle_time=1.2):
        self.driver = driver
        self.serial = serial
        self.app_package = app_package
        self.run_dir = run_dir
        self.log = step_logger
        self.max_pages = max_pages
        self.max_taps = max_taps
        self.max_depth = max_depth
        self.settle_time = settle_time

        self.pages = {}          # fingerprint -> {"title":, "screenshot":}
        self.edges = []          # (from_fp, action_label, to_fp)
        self.issues = []         # short summaries for the crawl SUMMARY.md
        self.taps_used = 0

    def _snapshot(self, fingerprint):
        shot_path = self.run_dir / "screenshots" / f"{fingerprint}.png"
        shot_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            media.screenshot(self.driver, shot_path)
        except Exception:
            shot_path = None
        return shot_path

    def _current_package(self):
        try:
            return self.driver.current_package
        except Exception:
            return None

    def _is_app_alive(self):
        return self._current_package() == self.app_package

    def _recover(self):
        """Force the device back to a known state: this app, freshly foregrounded."""
        try:
            self.driver.terminate_app(self.app_package)
        except Exception:
            pass
        time.sleep(1)
        try:
            self.driver.activate_app(self.app_package)
        except Exception:
            pass
        time.sleep(2)

    def _log_departure_issue(self, label, other_package, exc=None):
        """We ended up outside our own app package. Never keep interacting with whatever
        that other app is (could be the home screen, another installed app, a browser, etc)."""
        shot = None
        try:
            shot = self.run_dir / "screenshots" / f"departure_{int(time.time()*1000)}.png"
            media.screenshot(self.driver, shot)
        except Exception:
            shot = None

        log_text = dump_logcat(self.serial, self.app_package)
        crash_excerpt = find_crash(log_text)

        steps = self.log.path_so_far() + [f"Tapped '{label}' — app is no longer in foreground "
                                           f"(now showing '{other_package}')"]
        title = (f"App crashed/closed after tapping '{label}'" if crash_excerpt or other_package is None
                 else f"Tapping '{label}' navigated outside the app (to '{other_package}')")
        report_path = write_issue_report(
            self.run_dir,
            title=title,
            steps=steps,
            screenshot_path=str(shot) if shot else None,
            logcat_excerpt=crash_excerpt,
            error=exc,
            severity="Critical" if crash_excerpt else "Medium",
        )
        self.log.step(f"ISSUE LOGGED -> {report_path}")
        self.issues.append(f"{title} — see {report_path}")
        self._recover()

    def _try_return_to(self, fp, label, max_retries=2):
        """Press back and verify we land on `fp`. Many mismatches are transient (an extra
        toast/keyboard/tab-reselect to dismiss) rather than a real divergence, so retry the
        hardware back button a couple more times before giving up. Every press is checked for
        app/package safety before proceeding to the next — never taps anything blind.
        Returns True if we're confirmed back on `fp`, False otherwise (safe either way)."""
        for attempt in range(max_retries + 1):
            try:
                self.driver.back()
                time.sleep(self.settle_time)
            except Exception as e:
                self.log.step(f"Back navigation failed after '{label}' (attempt {attempt + 1}): {e} — recovering")
                self._recover()
                return False

            pkg_back = self._current_package()
            if pkg_back != self.app_package:
                self.log.step(f"Back navigation from '{label}' left the app "
                               f"(now '{pkg_back}') — recovering, abandoning this page")
                self._recover()
                return False

            try:
                back_fp = page_fingerprint(self.driver)
            except Exception as e:
                self.log.step(f"Could not verify page after back-nav: {e} — recovering")
                self._recover()
                return False

            if back_fp == fp:
                return True

            if attempt < max_retries:
                self.log.step(f"Back navigation from '{label}' landed on [{back_fp}], not [{fp}] yet "
                               f"— retrying back (attempt {attempt + 2}/{max_retries + 1})")

        self.log.step(f"Back navigation from '{label}' never returned to [{fp}] after "
                       f"{max_retries + 1} attempt(s) (last seen: [{back_fp}]) — abandoning "
                       f"remaining elements on this page rather than tapping blind")
        return False

    def crawl(self, depth=0):
        if len(self.pages) >= self.max_pages or self.taps_used >= self.max_taps:
            return
        if not self._is_app_alive():
            self.log.step("App not in foreground at crawl entry — recovering")
            self._recover()
            if not self._is_app_alive():
                return

        try:
            fp = page_fingerprint(self.driver)
        except Exception as e:
            self.log.step(f"Could not read page source: {e}")
            return

        if fp in self.pages:
            return

        title = page_title_guess(self.driver)
        shot = self._snapshot(fp)
        self.pages[fp] = {"title": title, "screenshot": str(shot) if shot else None}
        self.log.step(f"Discovered page [{fp}] '{title}' (depth {depth})")

        if depth >= self.max_depth:
            self.log.step(f"Max depth reached at [{fp}], not exploring further")
            return

        num_elements = len(get_clickable_elements(self.driver))
        for i in range(num_elements):
            if len(self.pages) >= self.max_pages or self.taps_used >= self.max_taps:
                return

            # Hard safety gate: never tap unless we can prove we're still on the exact
            # page we think we're on, inside our own app. If anything drifted (a stray
            # back-nav, a permission dialog, a deep link, the home screen) we stop
            # exploring this page immediately rather than blind-tapping by index.
            pkg = self._current_package()
            if pkg != self.app_package:
                self.log.step(f"Not in {self.app_package} before tapping element [{i}] "
                               f"(currently '{pkg}') — aborting this page, recovering")
                self._recover()
                return
            try:
                current_fp = page_fingerprint(self.driver)
            except Exception as e:
                self.log.step(f"Could not verify page before tap [{i}]: {e} — recovering")
                self._recover()
                return
            if current_fp != fp:
                self.log.step(f"Screen drifted from [{fp}] to [{current_fp}] before tapping "
                               f"element [{i}] — aborting this page, recovering")
                self._recover()
                return

            elements = get_clickable_elements(self.driver)
            if i >= len(elements):
                break
            el = elements[i]
            label = describe_element(el)

            try:
                self.log.step(f"Tapping element [{i}] '{label}' on page [{fp}]")
                el.click()
                self.taps_used += 1
                time.sleep(self.settle_time)
            except Exception as e:
                self.log.step(f"Tap failed on [{i}] '{label}': {e}")
                continue

            pkg_after = self._current_package()
            if pkg_after != self.app_package:
                self._log_departure_issue(label, pkg_after)
                return  # do not keep tapping — we can no longer trust what's on screen

            try:
                new_fp = page_fingerprint(self.driver)
            except Exception as e:
                self._log_departure_issue(label, pkg_after, exc=e)
                return

            if new_fp != fp:
                self.edges.append((fp, label, new_fp))
                self.crawl(depth=depth + 1)
                if not self._try_return_to(fp, label):
                    return
            else:
                self.log.step(f"Element [{i}] '{label}' had no visible effect (no-op or same page)")
