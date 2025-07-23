import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any

import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ReadmeGenerator:
    """Generates README.md file with ranked Python web frameworks from GitHub."""
    
    GITHUB_API_BASE = "https://api.github.com"
    REPO_LIST_FILE = "list.txt"
    OUTPUT_FILE = "README.md"
    HISTORY_JSON_FILE = "framework_stars_history.json"
    
    MARKDOWN_HEADER = '''# Top Python Web Frameworks
A list of popular github projects related to Python web framework (ranked by stars automatically)

* UPDATE **list.txt** (via Pull Request)

'''
    
    def _get_markdown_growth_trends(self, json_filename: str) -> str:
        """Get growth trends section with appropriate JSON filename."""
        template = '''
## 📊 Growth Trends

<div id="chartContainer">
  <div style="margin-bottom: 30px;">
    <canvas id="starsChart" width="800" height="400"></canvas>
  </div>
  <div style="margin-bottom: 30px;">
    <canvas id="forksChart" width="800" height="400"></canvas>
  </div>
  <div style="margin-bottom: 30px;">
    <canvas id="issuesChart" width="800" height="400"></canvas>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
<script>
// Load and display historical data
fetch('./JSONFILE')
  .then(response => response.json())
  .then(data => {
    const projects = data.projects;
    const topProjects = Object.keys(projects)
      .filter(name => projects[name].history.length > 0)
      .sort((a, b) => {
        const latestA = projects[a].history[projects[a].history.length - 1];
        const latestB = projects[b].history[projects[b].history.length - 1];
        return latestB.stars - latestA.stars;
      })
      .slice(0, 10);

    // Stars Chart
    const starsCtx = document.getElementById('starsChart').getContext('2d');
    new Chart(starsCtx, {{
      type: 'line',
      data: {{
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.stars
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'GitHub Stars Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Stars'
            }
          }
        }
      }
    });

    // Forks Chart
    const forksCtx = document.getElementById('forksChart').getContext('2d');
    new Chart(forksCtx, {
      type: 'line',
      data: {
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.forks
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'GitHub Forks Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Forks'
            }
          }
        }
      }
    });

    // Issues Chart
    const issuesCtx = document.getElementById('issuesChart').getContext('2d');
    new Chart(issuesCtx, {
      type: 'line',
      data: {
        datasets: topProjects.map((projectName, index) => ({
          label: projectName,
          data: projects[projectName].history.map(point => ({
            x: point.timestamp,
            y: point.open_issues
          })),
          borderColor: `hsl(${index * 36}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 36}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Open Issues Over Time (Top 10)'
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Open Issues'
            }
          }
        }
      }
    });
  })
  .catch(error => {
    console.error('Error loading chart data:', error);
    document.getElementById('chartContainer').innerHTML = '<p>Charts will be available after data collection.</p>';
  });
</script>
'''
        return template.replace('JSONFILE', json_filename)
    
    MARKDOWN_FOOTER_TEMPLATE = '\n*Last Automatic Update: {}*'
    def __init__(self):
        self.access_token = self._load_access_token()
        self.headers = {"Authorization": f"Token {self.access_token}"}
        self.repositories = []


    def _load_access_token(self) -> str:
        """Load GitHub access token from environment variable."""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise FileNotFoundError(
                "GitHub token not found. Set GITHUB_TOKEN environment variable"
            )
        return token.strip()
    
    def _validate_github_access(self) -> None:
        """Validate GitHub API access with current token."""
        test_url = f"{self.GITHUB_API_BASE}/repos/django/django"
        response = requests.get(test_url, headers=self.headers, verify=False)
        if response.status_code >= 300:
            raise ValueError(f'Cannot access GitHub API: {response.text}')
        logger.info("GitHub API access validated successfully")
    
    def _parse_repository_url(self, url: str) -> str:
        """Extract repository path from GitHub URL."""
        if not url.startswith('https://github.com/'):
            raise ValueError(f"Invalid GitHub URL: {url}")
        return url[19:]  # Remove 'https://github.com/'
    
    def _fetch_repository_data(self, repo_path: str) -> Dict[str, Any]:
        """Fetch repository data from GitHub API."""
        repo_url = f"{self.GITHUB_API_BASE}/repos/{repo_path}"
        response = requests.get(repo_url, headers=self.headers, verify=False)
        
        if response.status_code != 200:
            raise ValueError(f'Cannot retrieve repository data for {repo_path}: {response.text}')
        
        return response.json()
    
    def _fetch_latest_commit_date(self, repo_path: str, default_branch: str) -> str:
        """Fetch latest commit date from repository's default branch."""
        commit_url = f"{self.GITHUB_API_BASE}/repos/{repo_path}/commits/{default_branch}"
        response = requests.get(commit_url, headers=self.headers, verify=False)
        
        if response.status_code != 200:
            raise ValueError(f'Cannot retrieve commit data for {repo_path}: {response.text}')
        
        commit_data = response.json()
        return commit_data['commit']['committer']['date']
    
    def _load_repository_urls(self) -> List[str]:
        """Load repository URLs from list file."""
        try:
            with open(self.REPO_LIST_FILE, 'r') as f:
                urls = [url.strip() for url in f.readlines() if url.strip()]
                if not urls:
                    raise ValueError("Repository list is empty")
                return urls
        except FileNotFoundError:
            raise FileNotFoundError(f"Repository list file '{self.REPO_LIST_FILE}' not found")
    
    def fetch_all_repositories(self) -> None:
        """Fetch data for all repositories in the list."""
        self._validate_github_access()
        urls = self._load_repository_urls()
        
        logger.info(f"Processing {len(urls)} repositories...")
        
        for url in urls:
            try:
                repo_path = self._parse_repository_url(url)
                logger.info(f"Fetching data for {repo_path}")
                
                repo_data = self._fetch_repository_data(repo_path)
                commit_date = self._fetch_latest_commit_date(repo_path, repo_data['default_branch'])
                
                repo_data['last_commit_date'] = commit_date
                self.repositories.append(repo_data)
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                continue
        
        # Sort repositories by star count (descending)
        self.repositories.sort(key=lambda r: r['stargazers_count'], reverse=True)
        logger.info(f"Successfully processed {len(self.repositories)} repositories")
    
    def generate_readme(self, output_file: str = None, json_file: str = None) -> None:
        """Generate README.md file with repository data."""
        if not self.repositories:
            raise ValueError("No repository data available. Run fetch_all_repositories() first.")
        
        # Use provided filenames or defaults
        output_file = output_file or self.OUTPUT_FILE
        json_file = json_file or self.HISTORY_JSON_FILE
        
        logger.info(f"Generating {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.MARKDOWN_HEADER)
            
            # Add Current Rankings section first
            f.write('## 📈 Current Rankings\n\n')
            f.write('| Project Name | Stars | Forks | Open Issues | Last Commit |\n')
            f.write('| ------------ | ----- | ----- | ----------- | ----------- |\n')
            
            for repo in self.repositories:
                # Format last commit date
                commit_date = datetime.strptime(
                    repo['last_commit_date'], 
                    '%Y-%m-%dT%H:%M:%SZ'
                ).strftime('%Y-%m-%d %H:%M:%S')
                
                # Write repository row
                f.write(
                    f"| [{repo['name']}]({repo['html_url']}) | "
                    f"{repo['stargazers_count']} | "
                    f"{repo['forks_count']} | "
                    f"{repo['open_issues_count']} | "
                    f"{commit_date} |\n"
                )
            
            # Add Growth Trends section after the table
            f.write(self._get_markdown_growth_trends(json_file))
            
            # Add footer with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%Z')
            f.write(self.MARKDOWN_FOOTER_TEMPLATE.format(timestamp))
        
        logger.info(f"Successfully generated {output_file}")
    
    def _load_history_data(self, json_file: str = None) -> Dict[str, Any]:
        """Load existing history data from JSON file."""
        json_file = json_file or self.HISTORY_JSON_FILE
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info(f"History file {json_file} not found. Creating new one.")
            return {
                "metadata": {
                    "first_recorded": None,
                    "last_updated": None,
                    "total_snapshots": 0
                },
                "projects": {}
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            raise
    
    def _update_history_data(self, history_data: Dict[str, Any]) -> None:
        """Update history data with current repository information."""
        current_timestamp = datetime.now().isoformat() + 'Z'
        
        # Update metadata
        if history_data["metadata"]["first_recorded"] is None:
            history_data["metadata"]["first_recorded"] = current_timestamp
        history_data["metadata"]["last_updated"] = current_timestamp
        history_data["metadata"]["total_snapshots"] += 1
        
        # Update project data
        for repo in self.repositories:
            project_name = repo['name']
            
            # Initialize project if not exists
            if project_name not in history_data["projects"]:
                history_data["projects"][project_name] = {
                    "name": project_name,
                    "html_url": repo['html_url'],
                    "history": []
                }
            
            # Add current data point
            data_point = {
                "timestamp": current_timestamp,
                "stars": repo['stargazers_count'],
                "forks": repo['forks_count'],
                "open_issues": repo['open_issues_count'],
                "last_commit": repo['last_commit_date']
            }
            
            history_data["projects"][project_name]["history"].append(data_point)
            
            # Keep history sorted by timestamp
            history_data["projects"][project_name]["history"].sort(
                key=lambda x: x["timestamp"]
            )
        
        logger.info(f"Updated history data for {len(self.repositories)} projects")
    
    def _save_history_data(self, history_data: Dict[str, Any], json_file: str = None) -> None:
        """Save history data to JSON file."""
        json_file = json_file or self.HISTORY_JSON_FILE
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved history data to {json_file}")
        except Exception as e:
            logger.error(f"Failed to save history data: {e}")
            raise
    
    def generate_history_json(self, json_file: str = None) -> None:
        """Generate or update time-series JSON data for graph visualization."""
        if not self.repositories:
            raise ValueError("No repository data available. Run fetch_all_repositories() first.")
        
        json_file = json_file or self.HISTORY_JSON_FILE
        logger.info(f"Generating/updating {json_file}...")
        
        # Load existing history data
        history_data = self._load_history_data(json_file)
        
        # Update with current data
        self._update_history_data(history_data)
        
        # Save updated data
        self._save_history_data(history_data, json_file)
    
    def run(self) -> None:
        """Main execution method."""
        try:
            self.fetch_all_repositories()
            self.generate_readme()
            self.generate_history_json()
            
            logger.info("README and history JSON generation completed successfully")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise


def main():
    """Main entry point."""
    generator = ReadmeGenerator()
    generator.run()


if __name__ == '__main__':
    main()
