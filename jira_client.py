import requests
from typing import List, Any
from jira.client import ResultList
from jira.resources import Resource
from requests.auth import HTTPBasicAuth
from jira import JIRA, Issue, resources
from datetime import datetime
from config.app_config import AppConfig


class JiraClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.jira = JIRA(config.JIRA_SERVER, basic_auth=(config.JIRA_USERNAME, config.JIRA_API_KEY))
        self.auth = HTTPBasicAuth(config.JIRA_USERNAME, config.JIRA_API_KEY)

    def search_issues(self, start_at: int, max_results: int) -> ResultList[Issue]:
        jql = f"project = '{self.config.JIRA_PROJECT}' ORDER BY updated ASC"
        issues = self.jira.search_issues(jql, startAt=start_at, maxResults=max_results, expand='changelog, comment')
        return issues

    def fetch_histories(self, issueIdOrKey: str, start_at: int, max_results: int) -> Resource:
        url = f"{self.config.JIRA_SERVER}/rest/api/3/issue/{issueIdOrKey}/changelog"
        headers = {
            "Accept": "application/json"
        }
        response = requests.get(
            url,
            headers=headers,
            params={"startAt": start_at, "maxResults": max_results},
            auth=self.auth
        )
        return resources.dict2resource(response.json())

    def get_all_histories(self, issue: Issue) -> List[Any]:
        all_histories = issue.changelog.histories
        histories_start_at = 0
        histories_total = issue.changelog.total
        if histories_total > len(all_histories):
            while True:
                histories_remaining = histories_total - len(all_histories)
                if histories_remaining <= 0:
                    break
                histories_max_results = 100 if histories_remaining > 100 else histories_remaining
                result = self.fetch_histories(issue.key, start_at=histories_start_at,
                                              max_results=histories_max_results)

                if not result.values:
                    break

                histories = result.values
                all_histories.extend(histories)

                histories_start_at += histories_max_results

        return sorted(all_histories,
                      key=lambda x: datetime.strptime(x.created, '%Y-%m-%dT%H:%M:%S.%f%z'))
