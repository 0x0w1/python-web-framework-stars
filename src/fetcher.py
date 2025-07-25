#!/usr/bin/env python3
"""
Framework Trends Aggregator

Reads individual {owner}_{repo}.json files and generates aggregated trends data and README.
"""

import json
import os
from datetime import datetime
from typing import List


def load_repository_urls(filename: str = "list.txt") -> List[str]:
    """Load repository URLs from file."""
    try:
        with open(filename, "r") as f:
            urls = [url.strip() for url in f.readlines() if url.strip()]
            if not urls:
                raise ValueError("Repository list is empty")
            return urls
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filename}' not found")


def generate_history_json(repo_urls: List[str], output_file: str = "python_web_framework_trends.json") -> None:
    """Generate aggregated history JSON from individual repository files."""
    history_data = {"projects": {}}

    for url in repo_urls:
        try:
            # Extract owner and repo name from URL
            repo_path = url.replace("https://github.com/", "")
            owner, repo = repo_path.split("/")

            # Load individual repository data
            repo_file = f"repositories_information/{owner}_{repo}.json"

            if not os.path.exists(repo_file):
                print(f"Warning: {repo_file} not found, skipping...")
                continue

            with open(repo_file, "r", encoding="utf-8") as f:
                repo_data = json.load(f)

            # Create project entry if it doesn't exist
            project_name = repo
            if project_name not in history_data["projects"]:
                history_data["projects"][project_name] = {"name": project_name, "html_url": url, "history": []}

            # Add current data point to history
            history_entry = {
                "timestamp": repo_data.get("fetched_at", datetime.now().isoformat()),
                "stars": repo_data.get("total_stars", 0),
                "forks": repo_data.get("total_forks", 0),
                "open_issues": 0,  # Not available in fetcher data
                "last_commit": "",  # Not available in fetcher data
            }

            # Avoid duplicate entries by checking timestamp
            existing_timestamps = [entry["timestamp"] for entry in history_data["projects"][project_name]["history"]]
            if history_entry["timestamp"] not in existing_timestamps:
                history_data["projects"][project_name]["history"].append(history_entry)
                history_data["projects"][project_name]["history"].sort(key=lambda x: x["timestamp"])

        except Exception as e:
            print(f"Failed to process {url}: {e}")
            continue

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)

    print(f"Generated {output_file} with {len(history_data['projects'])} projects")


def generate_readme(trends_file: str = "python_web_framework_trends.json", output_file: str = "README.md") -> None:
    """Generate README.md file from trends data."""
    if not os.path.exists(trends_file):
        raise FileNotFoundError(f"Trends file '{trends_file}' not found")

    with open(trends_file, "r", encoding="utf-8") as f:
        trends_data = json.load(f)

    # Get latest data for each project and sort by stars
    projects = []
    for project_name, project_data in trends_data["projects"].items():
        if project_data["history"]:
            latest = project_data["history"][-1]  # Get latest entry
            projects.append(
                {
                    "name": project_name,
                    "html_url": project_data["html_url"],
                    "stars": latest["stars"],
                    "forks": latest["forks"],
                    "open_issues": latest["open_issues"],
                    "last_commit": latest["last_commit"],
                    "timestamp": latest["timestamp"],
                }
            )

    # Sort by stars (descending)
    projects.sort(key=lambda p: p["stars"], reverse=True)

    header = """# Top Python Web Frameworks
A list of popular github projects related to Python web framework (ranked by stars automatically)

* UPDATE **list.txt** (via Pull Request)

## 📈 Current Rankings

"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("| Project Name | Stars | Forks | Open Issues | Last Commit |\n")
        f.write("| ------------ | ----- | ----- | ----------- | ----------- |\n")

        for project in projects:
            # Format timestamp if available
            if project["last_commit"]:
                try:
                    commit_date = datetime.strptime(project["last_commit"], "%Y-%m-%dT%H:%M:%SZ").strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    commit_date = "N/A"
            else:
                commit_date = "N/A"

            f.write(
                f"| [{project['name']}]({project['html_url']}) | "
                f"{project['stars']} | "
                f"{project['forks']} | "
                f"{project['open_issues']} | "
                f"{commit_date} |\n"
            )

        # Add footer
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        f.write(f"\n*Last Automatic Update: {timestamp}*\n")

    print(f"Generated {output_file}")


def main():
    """Main execution function."""
    try:
        # Load repository URLs
        repo_urls = load_repository_urls()
        print(f"Loaded {len(repo_urls)} repository URLs")

        # Generate aggregated trends JSON from individual repository files
        generate_history_json(repo_urls)

        # Generate README from trends data
        generate_readme()

        print("All tasks completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
