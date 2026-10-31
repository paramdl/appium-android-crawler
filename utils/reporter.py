import json
import time
from pathlib import Path


def write_issue_report(run_dir, title, steps, screenshot_path=None, video_path=None,
                        logcat_excerpt=None, error=None, severity="High"):
    issues_dir = Path(run_dir) / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    issue_id = f"issue_{int(time.time() * 1000)}"
    issue_dir = issues_dir / issue_id
    issue_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {title}",
        "",
        f"**Severity:** {severity}",
        f"**Detected:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Steps to Reproduce",
    ]
    for i, s in enumerate(steps, 1):
        lines.append(f"{i}. {s}")

    if error:
        lines += ["", "## Error", "```", str(error), "```"]

    if screenshot_path:
        lines += ["", f"## Screenshot", f"![screenshot]({screenshot_path})"]

    if video_path:
        lines += ["", f"## Recording", f"{video_path}"]

    if logcat_excerpt:
        lines += ["", "## Logcat (crash excerpt)", "```", logcat_excerpt.strip(), "```"]

    report_path = issue_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    meta = {
        "title": title, "severity": severity, "steps": steps,
        "screenshot": screenshot_path, "video": video_path, "error": str(error) if error else None,
    }
    (issue_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return report_path


def write_crawl_summary(run_dir, pages, issues, edges):
    lines = [
        "# Crawl Summary",
        "",
        f"**Pages discovered:** {len(pages)}",
        f"**Issues found:** {len(issues)}",
        "",
        "## Pages",
    ]
    for fp, info in pages.items():
        lines.append(f"- `{fp}` — {info['title']} (screenshot: {info['screenshot']})")

    lines += ["", "## Navigation edges"]
    for from_fp, action, to_fp in edges:
        lines.append(f"- `{from_fp}` --[{action}]--> `{to_fp}`")

    if issues:
        lines += ["", "## Issues"]
        for issue in issues:
            lines.append(f"- {issue}")

    summary_path = Path(run_dir) / "SUMMARY.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path
