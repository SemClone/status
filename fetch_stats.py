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
    "upmex",
    "src2purl",
    "vulnq",
    "ospac",
    "mcp-semclone",
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


def calculate_last_day_from_overall(overall_data: Dict[str, Any]) -> Optional[int]:
    """
    Calculate last_day downloads from overall data.
    Returns the sum of downloads from the most recent date in the data.
    """
    if not overall_data or "data" not in overall_data:
        return None

    data = overall_data["data"]
    if not data:
        return None

    # Group downloads by date and sum across categories
    date_downloads = {}
    for entry in data:
        date = entry.get("date")
        downloads = entry.get("downloads", 0)
        if date:
            date_downloads[date] = date_downloads.get(date, 0) + downloads

    if not date_downloads:
        return None

    # Get the most recent date
    most_recent_date = max(date_downloads.keys())
    return date_downloads[most_recent_date]


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
        time.sleep(0.5)  # Small delay to avoid rate limiting
        overall = fetch_overall_stats(package)
        time.sleep(0.5)

        # Calculate last_day from overall data
        calculated_last_day = calculate_last_day_from_overall(overall)

        # Check for discrepancy and fix it
        api_last_day = None
        if recent and "data" in recent:
            api_last_day = recent["data"].get("last_day", 0)

            # If we have a calculated value and it differs from the API, use ours
            if calculated_last_day is not None and api_last_day != calculated_last_day:
                print(f"  ⚠️  Discrepancy detected: API reports {api_last_day}, calculated {calculated_last_day}")
                recent["data"]["last_day"] = calculated_last_day
                recent["data"]["_discrepancy_warning"] = {
                    "api_value": api_last_day,
                    "calculated_value": calculated_last_day,
                    "message": "last_day calculated from /overall data due to API staleness"
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
