#!/usr/bin/env python3
"""
GitHub Stars and Forks by Date Fetcher (Refactored)

This script fetches stargazers and forks data from GitHub API and outputs
star and fork counts grouped by date (yyyy-MM-dd) to a JSON file.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GitHubFetcher:
    def __init__(self, token=None):
        self.token = token
        self.headers = {
            "User-Agent": "Python-Stars-Forks-Fetcher",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    @staticmethod
    def get_token():
        """Get GitHub token from environment or file."""
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token

        try:
            with open("access_token.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            print("Warning: No GitHub token found. API rate limits will be lower.")
            return None

    @staticmethod
    def parse_url(url):
        """Parse GitHub URL to extract owner and repo."""
        path_parts = urlparse(url).path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        raise ValueError(f"Invalid GitHub URL format: {url}")

    def fetch_paginated_data(self, url, accept_header, start_page=1, params=None):
        """Generic function to fetch paginated data from GitHub API."""
        headers = self.headers.copy()
        headers["Accept"] = accept_header

        data = []
        page = start_page
        per_page = 100

        while True:
            request_params = {"page": page, "per_page": per_page}
            if params:
                request_params.update(params)

            try:
                response = requests.get(url, headers=headers, params=request_params, verify=False)
                response.raise_for_status()

                page_data = response.json()
                if not page_data:
                    break

                data.extend(page_data)
                print(f"Fetched page {page}, total items: {len(data)}")
                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
                break

        return data, page - 1

    def fetch_stargazers(self, owner, repo, start_page=1):
        """Fetch all stargazers with star dates."""
        url = f"https://api.github.com/repos/{owner}/{repo}/stargazers"
        return self.fetch_paginated_data(url, "application/vnd.github.v3.star+json", start_page)

    def fetch_forks(self, owner, repo, start_page=1):
        """Fetch all forks with creation dates."""
        url = f"https://api.github.com/repos/{owner}/{repo}/forks"
        return self.fetch_paginated_data(url, "application/vnd.github.v3+json", start_page, {"sort": "newest"})

    @staticmethod
    def group_by_date(items, date_field):
        """Group items by date."""
        grouped = defaultdict(int)
        for item in items:
            date_str = item.get(date_field)
            if date_str:
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_key = date_obj.strftime("%Y-%m-%d")
                grouped[date_key] += 1
        return dict(grouped)

    @staticmethod
    def load_existing_data(filename):
        """Load existing JSON data."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    @staticmethod
    def merge_data(existing_data, new_stars, new_forks, cutoff_date):
        """Merge new data with existing data from cutoff date."""
        if not existing_data:
            return new_stars, new_forks

        existing_stars = existing_data.get("stars_by_date", {})
        existing_forks = existing_data.get("forks_by_date", {})

        # Keep existing data before cutoff, add new data from cutoff onwards
        merged_stars = {d: c for d, c in existing_stars.items() if d < cutoff_date}
        merged_forks = {d: c for d, c in existing_forks.items() if d < cutoff_date}

        for date, count in new_stars.items():
            if date >= cutoff_date:
                merged_stars[date] = count

        for date, count in new_forks.items():
            if date >= cutoff_date:
                merged_forks[date] = count

        return merged_stars, merged_forks

    @staticmethod
    def save_data(data, filename):
        """Save data to JSON file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub stars and forks data by date")
    parser.add_argument("repo_url", help="GitHub repository URL")

    args = parser.parse_args()

    try:
        fetcher = GitHubFetcher(GitHubFetcher.get_token())
        owner, repo = fetcher.parse_url(args.repo_url)

        print(f"Fetching data for {owner}/{repo}...")

        # Setup output
        output_filename = f"repo_data/{owner}_{repo}.json"

        # Fetch data
        print("\n=== Fetching Stargazers ===")
        stargazers, _ = fetcher.fetch_stargazers(owner, repo)

        print("\n=== Fetching Forks ===")
        forks, _ = fetcher.fetch_forks(owner, repo)

        # Group by date
        stars_by_date = fetcher.group_by_date(stargazers, "starred_at")
        forks_by_date = fetcher.group_by_date(forks, "created_at")

        # Prepare output data
        total_stars = sum(stars_by_date.values()) or len(stargazers)
        total_forks = sum(forks_by_date.values()) or len(forks)

        output_data = {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "fetched_at": datetime.now().isoformat(),
            "stars_by_date": dict(sorted(stars_by_date.items())),
            "forks_by_date": dict(sorted(forks_by_date.items())),
        }

        fetcher.save_data(output_data, output_filename)

        # Print summary
        print(f"\nData saved to {output_filename}")
        print(f"Repository: {owner}/{repo}")
        print(f"Total stars: {total_stars}")
        print(f"Total forks: {total_forks}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
