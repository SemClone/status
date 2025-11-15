#!/usr/bin/env python3
"""
Fetch PyPI download statistics for SEMCL.ONE packages.
Data is fetched from pypistats.org API and saved as JSON for the dashboard.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List, Any

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


def fetch_json(url: str) -> Dict[str, Any]:
    """Fetch JSON data from a URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}")
        return {}
    except Exception as e:
        print(f"Error fetching {url}: {e}")
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


def main():
    """Fetch all stats for all packages and save to JSON."""
    print(f"Fetching stats for {len(PACKAGES)} packages...")

    all_stats = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "packages": {}
    }

    for package in PACKAGES:
        print(f"Fetching stats for {package}...")

        package_stats = {
            "name": package,
            "recent": fetch_recent_stats(package),
            "overall": fetch_overall_stats(package),
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
