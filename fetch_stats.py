#!/usr/bin/env python3
"""
Fetch PyPI download statistics for SEMCL.ONE packages.
Data is fetched from pypistats.org API and saved as JSON for the dashboard.
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# List of packages to track
PACKAGES = [
    "purl2src",
    "binarysniffer",
    "osslili",
    "purl2notices",
    "ossnotices",
    "upmex",
    "src2purl",
    "vulnq",
    "ospac",
    "mcp-semclone",
    "ossval",
    "ossbomer",
    "suphm",
]

BASE_URL = "https://pypistats.org/api/packages"


def fetch_json(url: str, max_retries: int = 3) -> Dict[str, Any]:
    """Fetch JSON data from a URL with retry logic for rate limiting."""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    print(f"  Rate limited, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  HTTP Error {e.code} for {url} (max retries reached)")
                    return {}
            else:
                print(f"  HTTP Error {e.code} for {url}")
                return {}
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return {}
    return {}


def fetch_recent_stats(package: str) -> Dict[str, Any]:
    """Fetch recent download stats (day, week, month)."""
    url = f"{BASE_URL}/{package}/recent"
    return fetch_json(url)


def fetch_overall_stats(package: str) -> Dict[str, Any]:
    """Fetch overall daily download time series."""
    url = f"{BASE_URL}/{package}/overall"
    return fetch_json(url)


def fetch_python_versions(package: str) -> Dict[str, Any]:
    """Fetch downloads by Python minor version."""
    url = f"{BASE_URL}/{package}/python_minor"
    return fetch_json(url)


def fetch_system_stats(package: str) -> Dict[str, Any]:
    """Fetch downloads by operating system."""
    url = f"{BASE_URL}/{package}/system"
    return fetch_json(url)


CATEGORIES = ("with_mirrors", "without_mirrors")

# pypistats.org only serves the last ~180 days from /overall, so a total summed
# from one response is a rolling window. Every run merges its daily rows into
# this file, and lifetime totals are summed from it instead.
HISTORY_FILE = "docs/data/history.json"


def load_history(path: str = HISTORY_FILE) -> Dict[str, Any]:
    """Load the accumulated daily history.

    A missing file is an empty history. A file that exists and cannot be read
    raises: starting again from empty would silently shrink every total to
    the 180-day window this file exists to get past.
    """
    try:
        with open(path) as f:
            history = json.load(f)
    except FileNotFoundError:
        return {"packages": {}}
    if not isinstance(history.get("packages"), dict):
        raise ValueError(f"{path} has no 'packages' object; refusing to overwrite it")
    return history


def save_history(history: Dict[str, Any], path: str = HISTORY_FILE) -> None:
    with open(path, "w") as f:
        json.dump(history, f, indent=1, sort_keys=True)
        f.write("\n")


def merge_overall_into_history(history: Dict[str, Any], package: str,
                               overall_data: Dict[str, Any]) -> int:
    """Merge one /overall response into the history. Returns rows merged.

    A day already in the history is overwritten, because pypistats revises
    recent days. A day absent from this response is kept, which is the point.
    """
    rows = (overall_data or {}).get("data") or []
    pkg = history["packages"].setdefault(package, {c: {} for c in CATEGORIES})
    merged = 0
    for entry in rows:
        category, date = entry.get("category"), entry.get("date")
        if category in CATEGORIES and date:
            pkg.setdefault(category, {})[date] = entry.get("downloads", 0) or 0
            merged += 1
    return merged


def totals_from_history(history: Dict[str, Any], package: str) -> Dict[str, Any]:
    """Lifetime totals for a package, from the accumulated history."""
    pkg = history["packages"].get(package) or {}
    with_m = pkg.get("with_mirrors") or {}
    without_m = pkg.get("without_mirrors") or {}
    dates = sorted(set(with_m) | set(without_m))
    return {
        "total": sum(with_m.values()),
        "total_with_mirrors": sum(with_m.values()),
        "total_without_mirrors": sum(without_m.values()),
        "total_since": dates[0] if dates else None,
    }


def _window(series: Dict[str, int], latest: str, days: int) -> int:
    """Sum the calendar days (latest - days, latest]. Missing days count as 0."""
    end = datetime.strptime(latest, "%Y-%m-%d").date()
    start = end - timedelta(days=days)
    return sum(v for d, v in series.items()
               if start < datetime.strptime(d, "%Y-%m-%d").date() <= end)


def calculate_metrics_from_overall(overall_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate last_day, last_week and last_month from one /overall response.

    In pypistats, with_mirrors is every download and without_mirrors is the
    subset that did not come from a mirror, so the headline figures are the
    with_mirrors ones. Adding the two categories together counts every organic
    download twice.

    Windows are calendar days ending on the latest day in the data, so a
    package with days of no downloads is not credited with older ones.
    """
    result = {f"{w}{suffix}": None
              for w in ("last_day", "last_week", "last_month")
              for suffix in ("", "_with_mirrors", "_without_mirrors")}

    rows = (overall_data or {}).get("data") or []
    series = {c: {} for c in CATEGORIES}
    for entry in rows:
        category, date = entry.get("category"), entry.get("date")
        if category in CATEGORIES and date:
            series[category][date] = series[category].get(date, 0) + (entry.get("downloads", 0) or 0)

    dates = set(series["with_mirrors"]) | set(series["without_mirrors"])
    if not dates:
        return result
    latest = max(dates)

    for name, days in (("last_day", 1), ("last_week", 7), ("last_month", 30)):
        for category in CATEGORIES:
            result[f"{name}_{category}"] = _window(series[category], latest, days)
        result[name] = result[f"{name}_with_mirrors"]
    return result


def main():
    """Fetch all stats for all packages and save to JSON."""
    print(f"Fetching stats for {len(PACKAGES)} packages...")

    all_stats = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "packages": {}
    }

    history = load_history()

    for package in PACKAGES:
        print(f"Fetching stats for {package}...")

        recent = fetch_recent_stats(package)
        time.sleep(1.0)  # Increased delay to avoid rate limiting
        overall = fetch_overall_stats(package)
        time.sleep(1.0)

        merged = merge_overall_into_history(history, package, overall)
        calculated = calculate_metrics_from_overall(overall)
        api = (recent or {}).get("data") or {}

        data = {}
        warnings = []
        if calculated["last_day"] is not None:
            data.update(calculated)
            # /recent counts without mirrors; compare it to the same figure.
            discrepancies = {
                m: {"api_value": api[m], "calculated_value": calculated[f"{m}_without_mirrors"]}
                for m in ("last_day", "last_week", "last_month")
                if m in api and api[m] != calculated[f"{m}_without_mirrors"]
            }
            if discrepancies:
                disc_msgs = [f"{k}({v['api_value']}→{v['calculated_value']})"
                             for k, v in discrepancies.items()]
                print(f"  ⚠️  /recent disagrees with /overall (organic): {', '.join(disc_msgs)}")
                data["_discrepancy_warning"] = {
                    "discrepancies": discrepancies,
                    "message": "/recent (without mirrors) differs from /overall; /overall used",
                }
        elif api:
            # No /overall today. /recent only has without-mirrors figures, so
            # say so rather than present them as the with-mirrors headline.
            for m in ("last_day", "last_week", "last_month"):
                data[m] = api.get(m)
                data[f"{m}_without_mirrors"] = api.get(m)
                data[f"{m}_with_mirrors"] = None
            warnings.append("/overall unavailable: last_* are without-mirrors figures from /recent")
        else:
            warnings.append("/overall and /recent both unavailable: no window metrics this run")

        if not merged:
            warnings.append("/overall unavailable: totals are from history as of the previous run")
            print("  ⚠️  No /overall data; totals carried from history")
        data.update(totals_from_history(history, package))
        if warnings:
            data["_fallback_warning"] = {"message": "; ".join(warnings)}

        recent = {"data": data, "package": package, "type": "recent_downloads"}

        package_stats = {
            "name": package,
            "recent": recent,
            "overall": overall,
            "python_versions": fetch_python_versions(package),
            "system": fetch_system_stats(package),
        }

        all_stats["packages"][package] = package_stats

    save_history(history)
    print(f"✓ History saved to {HISTORY_FILE}")

    # Save to JSON file
    output_file = "docs/data/stats.json"
    with open(output_file, "w") as f:
        json.dump(all_stats, f, indent=2)

    print(f"\n✓ Stats saved to {output_file}")
    print(f"Last updated: {all_stats['last_updated']}")

    # Print summary
    print("\n=== Download Summary ===")
    for package in PACKAGES:
        recent = all_stats["packages"][package]["recent"]
        if recent and "data" in recent:
            last_day = recent["data"].get("last_day") or 0
            last_week = recent["data"].get("last_week") or 0
            last_month = recent["data"].get("last_month") or 0
            total = recent["data"].get("total") or 0
            total_without_mirrors = recent["data"].get("total_without_mirrors") or 0
            since = recent["data"].get("total_since") or "-"
            print(f"{package:20} - Day: {last_day:,} | Week: {last_week:,} | Month: {last_month:,} | Total since {since}: {total:,} (organic: {total_without_mirrors:,})")
        else:
            print(f"{package:20} - No data available")


if __name__ == "__main__":
    main()
