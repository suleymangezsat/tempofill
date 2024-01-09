from datetime import datetime
from typing import List, Any, Dict

import requests

from config.app_config import AppConfig


class TempoClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.headers: Dict[str, str] = {
            'Authorization': f'Bearer {self.config.TEMPO_API_KEY}',
            'Content-Type': 'application/json'
        }
        self.base_url: str = "https://api.tempo.io/4"

    def get_worklogs(self, start_date: datetime, end_date: datetime) -> List[str]:
        url_get: str = f"{self.base_url}/worklogs"
        params: Dict[str, str] = {
            "from": start_date.strftime('%Y-%m-%d'),
            "to": end_date.strftime('%Y-%m-%d')
        }
        response: requests.Response = requests.get(url_get, headers=self.headers, params=params)
        worklogs: Dict[str, Any] = response.json()
        return [worklog['tempoWorklogId'] for worklog in worklogs['results']]

    def create_worklog(self, issue_id: str, key: str, work_type: str, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
        date_str: str = start_dt.strftime('%Y-%m-%d')
        time_str: str = start_dt.strftime('%H:%M:%S')
        new_data: Dict[str, Any] = {
            "authorAccountId": self.config.JIRA_ACCOUNT_ID,
            "issueId": issue_id,
            "startDate": date_str,
            "startTime": time_str,
            "description": f"{work_type} {key}",
            "timeSpentSeconds": int((end_dt - start_dt).total_seconds())
        }
        url_post: str = f"{self.base_url}/worklogs"
        post_response: requests.Response = requests.post(url_post, json=new_data, headers=self.headers)
        return post_response.json()

    def delete_worklog(self, worklog_id: str) -> int:
        url_delete: str = f"{self.base_url}/worklogs/{worklog_id}"
        response: requests.Response = requests.delete(url_delete, headers=self.headers)
        return response.status_code

    def remove_worklogs_in_range(self, start_date: datetime, end_date: datetime) -> None:
        worklog_ids: List[str] = self.get_worklogs(start_date, end_date)
        for worklog_id in worklog_ids:
            delete_status: int = self.delete_worklog(worklog_id)
            print(f"Deleted worklog {worklog_id}: Status {delete_status}")
