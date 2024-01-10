from .config_reader import ConfigReader


class AppConfig:
    def __init__(self):
        self.config_reader = ConfigReader()

        self.RUN_START_DATE = self.config_reader.get('run', 'start_date')
        self.RUN_END_DATE = self.config_reader.get('run', 'end_date')
        self.RUN_TIMEZONE = self.config_reader.get('run', 'timezone', fallback='UTC')

        self.JIRA_ACCOUNT_ID = self.config_reader.get('jira', 'account_id')
        self.JIRA_PROJECT = self.config_reader.get('jira', 'project')
        self.JIRA_SERVER = self.config_reader.get('jira', 'server')
        self.JIRA_USERNAME = self.config_reader.get_secure('jira', 'username', 'JIRA_USERNAME')
        self.JIRA_API_KEY = self.config_reader.get_secure('jira', 'api_key', 'JIRA_API_KEY')
        self.JIRA_MEETING_ISSUE_ID = self.config_reader.get('jira', 'meeting_issue_id')

        self.GCALENDAR_EMAIL = self.config_reader.get_secure('gcalendar', 'email', 'GCALENDAR_EMAIL')

        self.TEMPO_API_KEY = self.config_reader.get_secure('tempo', 'api_key', 'TEMPO_API_KEY')

        self.STARTED_WORK_STATES = self.config_reader.get('work_states', 'started_work_states', fallback='').split(', ')
        self.FINISHED_WORK_STATES = self.config_reader.get('work_states', 'finished_work_states', fallback='').split(', ')
        self.PRIORITY_ORDER = self.config_reader.get('work_states', 'priority_order', fallback='').split(', ')

        self.WORKDAY_START_HOUR = int(self.config_reader.get('work_schedule', 'workday_start_hour', fallback='9'))
        self.WORKDAY_DURATION_HOURS = int(self.config_reader.get('work_schedule', 'workday_duration_hours', fallback='8'))
        self.COMMENT_DURATION_HOURS = int(self.config_reader.get('work_schedule', 'comment_duration_hours', fallback='2'))