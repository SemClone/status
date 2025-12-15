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


def calculate_metrics_from_overall(overall_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate last_day, last_week, last_month, and total cumulative downloads from overall data.
    Returns a dict with calculated values for both with_mirrors and without_mirrors.
    """
    result = {
        "last_day": None,
        "last_week": None,
        "last_month": None,
        "total": None,
        "last_day_with_mirrors": None,
        "last_week_with_mirrors": None,
        "last_month_with_mirrors": None,
        "total_with_mirrors": None,
        "last_day_without_mirrors": None,
        "last_week_without_mirrors": None,
        "last_month_without_mirrors": None,
        "total_without_mirrors": None
    }

    if not overall_data or "data" not in overall_data:
        return result

    data = overall_data["data"]
    if not data:
        return result

    # Group downloads by date and category
    date_downloads_all = {}
    date_downloads_with = {}
    date_downloads_without = {}

    for entry in data:
        date = entry.get("date")
        downloads = entry.get("downloads", 0)
        category = entry.get("category", "")

        if date:
            # Total (all categories)
            date_downloads_all[date] = date_downloads_all.get(date, 0) + downloads

            # Split by category
            if category == "with_mirrors":
                date_downloads_with[date] = date_downloads_with.get(date, 0) + downloads
            elif category == "without_mirrors":
                date_downloads_without[date] = date_downloads_without.get(date, 0) + downloads

    if not date_downloads_all:
        return result

    # Get the most recent dates
    sorted_dates = sorted(date_downloads_all.keys(), reverse=True)
    if not sorted_dates:
        return result

    # Calculate metrics for all categories combined
    result["last_day"] = date_downloads_all[sorted_dates[0]]
    result["last_week"] = sum(date_downloads_all.get(d, 0) for d in sorted_dates[:7])
    result["last_month"] = sum(date_downloads_all.get(d, 0) for d in sorted_dates[:30])
    result["total"] = sum(date_downloads_all.values())

    # Calculate metrics for with_mirrors
    result["last_day_with_mirrors"] = sum(date_downloads_with.get(d, 0) for d in sorted_dates[:1])
    result["last_week_with_mirrors"] = sum(date_downloads_with.get(d, 0) for d in sorted_dates[:7])
    result["last_month_with_mirrors"] = sum(date_downloads_with.get(d, 0) for d in sorted_dates[:30])
    result["total_with_mirrors"] = sum(date_downloads_with.values())

    # Calculate metrics for without_mirrors
    result["last_day_without_mirrors"] = sum(date_downloads_without.get(d, 0) for d in sorted_dates[:1])
    result["last_week_without_mirrors"] = sum(date_downloads_without.get(d, 0) for d in sorted_dates[:7])
    result["last_month_without_mirrors"] = sum(date_downloads_without.get(d, 0) for d in sorted_dates[:30])
    result["total_without_mirrors"] = sum(date_downloads_without.values())

    return result


def main():
    """Fetch all stats for all packages and save to JSON."""
    print(f"Fetching stats for {len(PACKAGES)} packages...")

    all_stats = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "packages": {}
    }

    for package in PACKAGES:
        print(f"Fetching stats for {package}...")

        recent = fetch_recent_stats(package)
        time.sleep(1.0)  # Increased delay to avoid rate limiting
        overall = fetch_overall_stats(package)
        time.sleep(1.0)

        # Calculate all metrics from overall data
        calculated_metrics = calculate_metrics_from_overall(overall)

        # If recent failed but we have overall data, create recent from calculated metrics
        if not recent or "data" not in recent:
            if any(v is not None for v in calculated_metrics.values()):
                print(f"  ℹ️  Using calculated metrics (API unavailable)")
                recent = {
                    "data": {
                        "last_day": calculated_metrics.get("last_day", 0),
                        "last_week": calculated_metrics.get("last_week", 0),
                        "last_month": calculated_metrics.get("last_month", 0),
                        "total": calculated_metrics.get("total", 0),
                        "last_day_with_mirrors": calculated_metrics.get("last_day_with_mirrors", 0),
                        "last_week_with_mirrors": calculated_metrics.get("last_week_with_mirrors", 0),
                        "last_month_with_mirrors": calculated_metrics.get("last_month_with_mirrors", 0),
                        "total_with_mirrors": calculated_metrics.get("total_with_mirrors", 0),
                        "last_day_without_mirrors": calculated_metrics.get("last_day_without_mirrors", 0),
                        "last_week_without_mirrors": calculated_metrics.get("last_week_without_mirrors", 0),
                        "last_month_without_mirrors": calculated_metrics.get("last_month_without_mirrors", 0),
                        "total_without_mirrors": calculated_metrics.get("total_without_mirrors", 0)
                    },
                    "package": package,
                    "type": "recent_downloads"
                }
                recent["data"]["_fallback_warning"] = {
                    "message": "All metrics calculated from /overall data (API unavailable)"
                }
        else:
            # Check for discrepancies and fix them
            discrepancies = {}

            for metric in ["last_day", "last_week", "last_month"]:
                api_value = recent["data"].get(metric, 0)
                calculated_value = calculated_metrics.get(metric)

                if calculated_value is not None and api_value != calculated_value:
                    discrepancies[metric] = {
                        "api_value": api_value,
                        "calculated_value": calculated_value
                    }
                    recent["data"][metric] = calculated_value

            # Always add mirror-specific metrics and totals
            recent["data"]["last_day_with_mirrors"] = calculated_metrics.get("last_day_with_mirrors", 0)
            recent["data"]["last_week_with_mirrors"] = calculated_metrics.get("last_week_with_mirrors", 0)
            recent["data"]["last_month_with_mirrors"] = calculated_metrics.get("last_month_with_mirrors", 0)
            recent["data"]["total_with_mirrors"] = calculated_metrics.get("total_with_mirrors", 0)
            recent["data"]["last_day_without_mirrors"] = calculated_metrics.get("last_day_without_mirrors", 0)
            recent["data"]["last_week_without_mirrors"] = calculated_metrics.get("last_week_without_mirrors", 0)
            recent["data"]["last_month_without_mirrors"] = calculated_metrics.get("last_month_without_mirrors", 0)
            recent["data"]["total_without_mirrors"] = calculated_metrics.get("total_without_mirrors", 0)
            recent["data"]["total"] = calculated_metrics.get("total", 0)

            # Report discrepancies
            if discrepancies:
                disc_msgs = [f"{k}({v['api_value']}→{v['calculated_value']})"
                            for k, v in discrepancies.items()]
                print(f"  ⚠️  Discrepancy: {', '.join(disc_msgs)}")
                recent["data"]["_discrepancy_warning"] = {
                    "discrepancies": discrepancies,
                    "message": "Metrics calculated from /overall data due to API staleness"
                }

        package_stats = {
            "name": package,
            "recent": recent,
            "overall": overall,
            "python_versions": fetch_python_versions(package),
            "system": fetch_system_stats(package),
        }

        all_stats["packages"][package] = package_stats

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
            last_day = recent["data"].get("last_day", 0)
            last_week = recent["data"].get("last_week", 0)
            last_month = recent["data"].get("last_month", 0)
            print(f"{package:20} - Day: {last_day:,} | Week: {last_week:,} | Month: {last_month:,}")
        else:
            print(f"{package:20} - No data available")


if __name__ == "__main__":
    main()
