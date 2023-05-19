from datetime import datetime
import json
import requests

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)


head = '''# Top Python Web Frameworks
A list of popular github projects related to Python web framework (ranked by stars automatically)

* ADD access_token.txt into this repository.
* UPDATE **list.txt** (via Pull Request)

| Project Name | Stars | Forks | Open Issues | Description | Last Commit |
| ------------ | ----- | ----- | ----------- | ----------- | ----------- |
'''
tail = '\n*Last Automatic Update: {}*'

warning = "⚠️ No longer maintained ⚠️  "

deprecated_repos = list()
repos = list()


API_URLS = {
    "repos": "https://api.github.com/repos/{}",
    "commit": "https://api.github.com/repos/{}/commits/{}"
}


def main():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Token {access_token}"
    }

    response = requests.get("https://api.github.com/repos/django/django", headers=headers, verify=False)
    if response.status_code >= 300:
        raise ValueError(f'Cannot access : {response.text}')

    with open('list.txt', 'r') as f:
        for url in f.readlines():
            repository = get_repos(url.strip())
            print(f"[+] Get {repository} stars & commits")

            if url.startswith('https://github.com/'):
                repo_resp = requests.get(url=API_URLS.get("repos").format(repository), headers=headers, verify=False)
                if repo_resp.status_code != 200:
                    raise ValueError('Can not retrieve from {}'.format(repository))
                repo = json.loads(repo_resp.content)

                r = requests.get(API_URLS.get("commit").format(repository, repo['default_branch']), headers=headers, verify=False)
                if r.status_code != 200:
                    raise ValueError('Can not retrieve from {}'.format(repository))
                commit = json.loads(r.content)

                repo['last_commit_date'] = commit['commit']['committer']['date']
                repos.append(repo)

        repos.sort(key=lambda r: r['stargazers_count'], reverse=True)
        save_ranking(repos)


def get_repos(url):
    return url[19:]


def get_access_token():
    with open('access_token.txt', 'r') as f:
        return f.read().strip()


def save_ranking(repos):
    with open('README.md', 'w') as f:
        f.write(head)
        for repo in repos:
            if is_deprecated(repo['url']):
                repo['description'] = warning + repo['description']
            f.write('| [{}]({}) | {} | {} | {} | {} | {} |\n'.format(repo['name'],
                                                                     repo['html_url'],
                                                                     repo['stargazers_count'],
                                                                     repo['forks_count'],
                                                                     repo['open_issues_count'],
                                                                     repo['description'],
                                                                     datetime.strptime(repo['last_commit_date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')))
        f.write(tail.format(datetime.now().strftime('%Y-%m-%dT%H:%M:%S%Z')))


def is_deprecated(repo_url):
    return repo_url in deprecated_repos


if __name__ == '__main__':
    main()
