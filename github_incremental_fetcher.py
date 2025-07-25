#!/usr/bin/env python3
"""
GitHub Stars and Forks by Date Fetcher

This script fetches stargazers and forks data from GitHub API and outputs
star and fork counts grouped by date (yyyy-MM-dd) to a JSON file.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import os
import sys
import argparse
from urllib.parse import urlparse
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_github_token():
    """Get GitHub token from environment variable or access_token.txt file."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    try:
        with open("access_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Warning: No GitHub token found. API rate limits will be lower.")
        return None


def parse_github_url(url):
    """Parse GitHub URL to extract owner and repo name."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    else:
        raise ValueError(f"Invalid GitHub URL format: {url}")


def is_recent_data(data_list, data_type="stargazers"):
    """Check if the latest data is within the last 7 days."""
    if not data_list:
        return False

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    # Get the date field based on data type
    date_field = "starred_at" if data_type == "stargazers" else "created_at"

    # Check the latest item's date
    latest_item = data_list[-1] if data_list else None
    if latest_item and latest_item.get(date_field):
        try:
            latest_date_str = latest_item[date_field]
            latest_date = datetime.fromisoformat(
                latest_date_str.replace("Z", "+00:00")
            ).date()
            return seven_days_ago <= latest_date <= today
        except (ValueError, TypeError):
            return False

    return False


def fetch_stargazers(owner, repo, token=None, start_page=1):
    """Fetch all stargazers for a repository with their star dates."""
    url = f"https://api.github.com/repos/{owner}/{repo}/stargazers"
    headers = {
        "Accept": "application/vnd.github.v3.star+json",
        "User-Agent": "Python-Stars-Forks-Fetcher",
    }

    if token:
        headers["Authorization"] = f"token {token}"

    stargazers = []
    page = start_page
    last_page = 0
    per_page = 100

    while True:
        params = {"page": page, "per_page": per_page}

        try:
            response = requests.get(url, headers=headers, params=params, verify=False)

            # Check if we should retry based on status code and data recency
            if response.status_code != 200:
                # Get current data to check if it's recent
                if stargazers and not is_recent_data(stargazers, "stargazers"):
                    print(
                        f"Non-200 status ({response.status_code}) but data is not recent. Sleeping 10 seconds..."
                    )
                    time.sleep(10)
                    continue
                else:
                    response.raise_for_status()

            data = response.json()
            if not data:
                break

            stargazers.extend(data)
            print(
                f"Fetched stargazers page {page}, total stargazers so far: {len(stargazers)}"
            )

            last_page = page
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching stargazers: {e}")
            break

    return stargazers, last_page


def fetch_forks(owner, repo, token=None, start_page=1):
    """Fetch all forks for a repository with their creation dates."""
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Stars-Forks-Fetcher",
    }

    if token:
        headers["Authorization"] = f"token {token}"

    forks = []
    page = start_page
    last_page = 0
    per_page = 100

    while True:
        params = {"page": page, "per_page": per_page, "sort": "newest"}

        try:
            response = requests.get(url, headers=headers, params=params, verify=False)

            # Check if we should retry based on status code and data recency
            if response.status_code != 200:
                # Get current data to check if it's recent
                if forks and not is_recent_data(forks, "forks"):
                    print(
                        f"Non-200 status ({response.status_code}) but data is not recent. Sleeping 10 seconds..."
                    )
                    time.sleep(10)
                    continue
                else:
                    response.raise_for_status()

            data = response.json()
            if not data:
                break

            forks.extend(data)
            print(f"Fetched forks page {page}, total forks so far: {len(forks)}")

            last_page = page
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching forks: {e}")
            break

    return forks, last_page


def group_stars_by_date(stargazers):
    """Group stargazers by date (yyyy-MM-dd format)."""
    stars_by_date = defaultdict(int)

    for stargazer in stargazers:
        starred_at = stargazer.get("starred_at")
        if starred_at:
            # Parse ISO datetime and extract date
            date_obj = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
            date_str = date_obj.strftime("%Y-%m-%d")
            stars_by_date[date_str] += 1

    return dict(stars_by_date)


def group_forks_by_date(forks):
    """Group forks by date (yyyy-MM-dd format)."""
    forks_by_date = defaultdict(int)

    for fork in forks:
        created_at = fork.get("created_at")
        if created_at:
            # Parse ISO datetime and extract date
            date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = date_obj.strftime("%Y-%m-%d")
            forks_by_date[date_str] += 1

    return dict(forks_by_date)


def load_existing_json(filename):
    """Load existing JSON data if it exists."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def merge_data_by_date(
    existing_data, new_stars_by_date, new_forks_by_date, cutoff_date
):
    """Merge new data with existing data from cutoff_date onwards."""
    if not existing_data:
        return new_stars_by_date, new_forks_by_date

    existing_stars = existing_data.get("stars_by_date", {})
    existing_forks = existing_data.get("forks_by_date", {})

    # Filter existing data to keep only dates before cutoff_date
    filtered_stars = {
        date: count for date, count in existing_stars.items() if date < cutoff_date
    }
    filtered_forks = {
        date: count for date, count in existing_forks.items() if date < cutoff_date
    }

    # Add new data (from cutoff_date onwards)
    for date, count in new_stars_by_date.items():
        if date >= cutoff_date:
            filtered_stars[date] = count

    for date, count in new_forks_by_date.items():
        if date >= cutoff_date:
            filtered_forks[date] = count

    return filtered_stars, filtered_forks


def save_to_json(data, filename):
    """Save data to JSON file without indentation."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub stars and forks data by date"
    )
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument(
        "--last-stargazers-page",
        type=int,
        help="Last stargazers page number for incremental update",
    )
    parser.add_argument(
        "--last-forks-page",
        type=int,
        help="Last forks page number for incremental update",
    )

    args = parser.parse_args()

    try:
        owner, repo = parse_github_url(args.repo_url)
        print(f"Fetching data for {owner}/{repo}...")

        token = get_github_token()

        # Create repository_informations directory if it doesn't exist
        output_dir = "repositories_information"
        os.makedirs(output_dir, exist_ok=True)

        # Create output filename with directory path
        output_filename = os.path.join(output_dir, f"{owner}_{repo}.json")

        # Load existing data if available
        existing_data = load_existing_json(output_filename)

        # Calculate start pages for incremental updates
        stargazers_start_page = 1
        forks_start_page = 1
        cutoff_date = None

        if args.last_stargazers_page:
            stargazers_start_page = max(1, args.last_stargazers_page - 2)
            print(
                f"Starting stargazers fetch from page {stargazers_start_page} (last page was {args.last_stargazers_page})"
            )

        if args.last_forks_page:
            forks_start_page = max(1, args.last_forks_page - 2)
            print(
                f"Starting forks fetch from page {forks_start_page} (last page was {args.last_forks_page})"
            )

        # If incremental update, calculate cutoff date
        if existing_data and (args.last_stargazers_page or args.last_forks_page):
            existing_stars_dates = existing_data.get("stars_by_date", {}).keys()
            existing_forks_dates = existing_data.get("forks_by_date", {}).keys()

            all_dates = list(existing_stars_dates) + list(existing_forks_dates)
            if all_dates:
                last_date = max(all_dates)
                cutoff_date_obj = datetime.strptime(last_date, "%Y-%m-%d") + timedelta(
                    days=1
                )
                cutoff_date = cutoff_date_obj.strftime("%Y-%m-%d")
                print(f"Incremental update: will merge data from {cutoff_date} onwards")

        # Fetch stargazers
        print("\n=== Fetching Stargazers ===")
        stargazers, last_stargazers_page = fetch_stargazers(
            owner, repo, token, stargazers_start_page
        )

        if not stargazers:
            print("No stargazers found or error occurred.")
            sys.exit(1)

        print(f"Total stargazers fetched: {len(stargazers)}")

        # Fetch forks
        print("\n=== Fetching Forks ===")
        forks, last_forks_page = fetch_forks(owner, repo, token, forks_start_page)

        print(f"Total forks fetched: {len(forks)}")

        # Group data by date
        new_stars_by_date = group_stars_by_date(stargazers)
        new_forks_by_date = group_forks_by_date(forks)

        # Merge with existing data if doing incremental update
        if cutoff_date:
            stars_by_date, forks_by_date = merge_data_by_date(
                existing_data, new_stars_by_date, new_forks_by_date, cutoff_date
            )
            print(
                f"Merged data: keeping existing data before {cutoff_date}, updating from {cutoff_date} onwards"
            )
        else:
            stars_by_date = new_stars_by_date
            forks_by_date = new_forks_by_date

        # Calculate total stars (sum of all stars by date)
        total_stars = sum(stars_by_date.values()) if stars_by_date else len(stargazers)

        # Prepare final data structure with specific order
        output_data = OrderedDict(
            [
                ("total_stars", total_stars),
                ("fetched_at", datetime.now().isoformat()),
                ("per_page", 100),
                ("last_stargazers_page", last_stargazers_page),
                ("last_forks_page", last_forks_page),
                (
                    "stars_by_date",
                    OrderedDict(sorted(stars_by_date.items()))
                    if stars_by_date
                    else OrderedDict(),
                ),
                (
                    "forks_by_date",
                    OrderedDict(sorted(forks_by_date.items()))
                    if forks_by_date
                    else OrderedDict(),
                ),
            ]
        )

        save_to_json(output_data, output_filename)
        print(f"\nData saved to {output_filename}")

        # Print summary
        print(f"\nSummary:")
        print(f"Repository: {owner}/{repo}")
        print(f"Total stars: {total_stars}")
        print(
            f"Total forks: {sum(forks_by_date.values()) if forks_by_date else len(forks)}"
        )
        print(f"Last stargazers page: {last_stargazers_page}")
        print(f"Last forks page: {last_forks_page}")
        if stars_by_date:
            print(
                f"Stars date range: {min(stars_by_date.keys())} to {max(stars_by_date.keys())}"
            )
            print(f"Days with stars: {len(stars_by_date)}")
        if forks_by_date:
            print(
                f"Forks date range: {min(forks_by_date.keys())} to {max(forks_by_date.keys())}"
            )
            print(f"Days with forks: {len(forks_by_date)}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
