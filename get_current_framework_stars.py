import logging
import os
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
    ACCESS_TOKEN_FILE = "access_token.txt"
    OUTPUT_FILE = "README.md"
    
    MARKDOWN_HEADER = '''# Top Python Web Frameworks
A list of popular github projects related to Python web framework (ranked by stars automatically)

* ADD access_token.txt into this repository.
* UPDATE **list.txt** (via Pull Request)

| Project Name | Stars | Forks | Open Issues | Last Commit |
| ------------ | ----- | ----- | ----------- | ----------- |
'''
    
    MARKDOWN_FOOTER_TEMPLATE = '\n*Last Automatic Update: {}*'
    def __init__(self):
        self.access_token = self._load_access_token()
        self.headers = {"Authorization": f"Token {self.access_token}"}
        self.repositories = []


    def _load_access_token(self) -> str:
        """Load GitHub access token from environment variable or file."""
        # First try to get token from environment variable (for GitHub Actions)
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token.strip()
        
        # Fallback to file for local development
        try:
            with open(self.ACCESS_TOKEN_FILE, 'r') as f:
                token = f.read().strip()
                if not token:
                    raise ValueError("Access token is empty")
                return token
        except FileNotFoundError:
            raise FileNotFoundError(
                f"GitHub token not found. Set GITHUB_TOKEN environment variable "
                f"or create '{self.ACCESS_TOKEN_FILE}' file"
            )
    
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
    
    def generate_readme(self) -> None:
        """Generate README.md file with repository data."""
        if not self.repositories:
            raise ValueError("No repository data available. Run fetch_all_repositories() first.")
        
        logger.info(f"Generating {self.OUTPUT_FILE}...")
        
        with open(self.OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(self.MARKDOWN_HEADER)
            
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
            
            # Add footer with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%Z')
            f.write(self.MARKDOWN_FOOTER_TEMPLATE.format(timestamp))
        
        logger.info(f"Successfully generated {self.OUTPUT_FILE}")
    
    def run(self) -> None:
        """Main execution method."""
        try:
            self.fetch_all_repositories()
            self.generate_readme()
            logger.info("README generation completed successfully")
        except Exception as e:
            logger.error(f"README generation failed: {e}")
            raise


def main():
    """Main entry point."""
    generator = ReadmeGenerator()
    generator.run()


if __name__ == '__main__':
    main()
