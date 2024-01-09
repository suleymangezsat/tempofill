import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Any, Literal

import pytz
from jira import Issue

from gcalendar import gcalendar
from config.app_config import AppConfig
from jira_client.jira_client import JiraClient
from models.activity import Activity
from tempo.tempo_client import TempoClient

config = AppConfig()
jira_client = JiraClient(config)
tempo_client = TempoClient(config)
calendar_service = gcalendar.get_calendar_service()
tz = pytz.timezone(config.RUN_TIMEZONE)


def fill_tempo():
    ongoing_issues = []

    worklog_from_date = datetime.strptime(config.RUN_START_DATE, '%Y-%m-%d').replace(
        tzinfo=tz)
    worklog_to_date = datetime.strptime(config.RUN_END_DATE, '%Y-%m-%d').replace(
        tzinfo=tz)

    jira_activities = process_issues(ongoing_issues)

    calendar_activities = process_calendar_events(worklog_from_date, worklog_to_date)

    sorted_activities = sorted(jira_activities + calendar_activities, key=lambda x: x.start_time)

    activity_by_day = organize_activities(sorted_activities)

    tempo_logs = []

    for day, day_activities in activity_by_day.items():
        day_start, day_end = get_day_time_bounds(day)

        adjusted_list = []
        for act_type in config.PRIORITY_ORDER:
            existing_acts = [a for a in day_activities if a.type == act_type]
            if existing_acts:
                for existing in existing_acts:
                    start_time, end_time = adjust_activity_times(existing, day_start, day_end)
                    add_to_adjusted(adjusted_list, existing, start_time, end_time)

        for adjusted in adjusted_list:
            start_time = adjusted.start_time
            end_time = adjusted.end_time
            if start_time >= worklog_from_date and end_time <= worklog_to_date:
                tempo_logs.append(Activity(
                    id=adjusted.id,
                    key=adjusted.key,
                    type=adjusted.type,
                    start_time=adjusted.start_time.astimezone(tz).isoformat(),
                    end_time=adjusted.end_time.astimezone(tz).isoformat()
                ))

    # Result: JSON for Tempo
    print(json.dumps([activity.to_dict() for activity in tempo_logs], indent=4))
    for tempo_log in tempo_logs:
        start_time = tempo_log.start_time
        end_time = tempo_log.end_time
        # Define new data to create
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        post_response_json = tempo_client.create_worklog(tempo_log.id, tempo_log.key,
                                                         tempo_log.type,
                                                         start_dt, end_dt)
        print(post_response_json)


def process_issues(ongoing_issues: List[str] = None, start_at: int = 0, max_results: int = 100) -> List[Activity]:
    if ongoing_issues is None:
        ongoing_issues = []
    issue_work: Dict[str, List[Activity]] = dict()
    while True:
        issues = jira_client.search_issues(start_at=start_at, max_results=max_results)
        if not issues:
            break

        for issue in issues:
            histories = jira_client.get_all_histories(issue)
            # Process each history in the current batch
            for history in histories:
                process_history_items(issue, history, issue_work)
            update_ongoing_issues(issue, issue_work, ongoing_issues)
            process_issue_comments(issue, issue_work)
        start_at += max_results
    return [item for sublist in issue_work.values() for item in sublist if
            item.start_time is not None and item.end_time is not None]


def process_calendar_events(calendar_start_date: datetime, calendar_end_date: datetime) -> List[Activity]:
    calendar_start_datetime = calendar_start_date.isoformat()
    calendar_end_datetime = calendar_end_date.isoformat()
    calendar_issues = []

    events_result = calendar_service.events().list(calendarId='primary', timeMin=calendar_start_datetime,
                                                   timeMax=calendar_end_datetime,
                                                   maxResults=1000, singleEvents=True,
                                                   orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        if is_invite_accepted(event):
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            calendar_issues.append(Activity(
                id=190786,
                key=event['summary'],
                type="Meeting",
                start_time=datetime.fromisoformat(start),
                end_time=datetime.fromisoformat(end)
            ))
    return calendar_issues


def organize_activities(activities: List[Activity]) -> Dict[datetime.date, List[Activity]]:
    activity_by_day = defaultdict(list)

    for act in (broken_act for act in activities for broken_act in break_into_days(act) if
                broken_act.key != 'Out of office'):
        day_key = act.start_time.date()
        activity_by_day[day_key].append(act)

    return activity_by_day


def adjust_activity_times(activity: Activity, day_start: datetime, day_end: datetime) -> Tuple[datetime, datetime]:
    start_time, end_time = activity.start_time, activity.end_time
    if activity.type != 'Meeting':
        delta = end_time - start_time
        start_time = max(start_time, day_start)
        end_time = min(end_time, day_end)
        if end_time < day_start:
            end_time = day_start + delta
        if start_time > day_end:
            start_time = day_end - delta
    return start_time, end_time


def get_day_time_bounds(day: datetime.date) -> Tuple[datetime, datetime]:
    day_start = datetime.combine(day, datetime.min.time()) + timedelta(hours=config.WORKDAY_START_HOUR)
    day_start = day_start.replace(tzinfo=tz)
    day_end = day_start + timedelta(hours=config.WORKDAY_DURATION_HOURS)
    return day_start, day_end


def process_history_items(issue: Issue, history: Any, issue_work: Dict[str, List[Activity]]) -> None:
    assigned_to_me = is_assigned(history, 'to')
    assigned_from_me = is_assigned(history, 'from')

    if history.author.accountId == config.JIRA_ACCOUNT_ID or assigned_to_me or assigned_from_me:
        for item in history.items:
            if item.field == 'status':
                add_issue_work(issue_work, issue, item, history, assigned_to_me, assigned_from_me)
                print(
                    f"Changelog - {history.created} - Issue: {issue.key}, Field: {item.field}, From: {item.fromString}, To: {item.toString}")
            elif item.field == 'assignee' and len(history.items) == 1 and assigned_from_me:
                history_created = datetime.strptime(history.created, '%Y-%m-%dT%H:%M:%S.%f%z')
                current_issue = issue_work.get(issue.key)
                if current_issue:
                    work = find_closest(current_issue, history_created)
                    if not work.end_time:
                        work.end_time = history_created


def find_closest(activities: List[Activity], target_date: datetime) -> Activity:
    min_diff = float('inf')
    closest_element = None

    for element in activities:
        if element.start_time:
            start_time = element.start_time

            diff = abs((start_time - target_date).total_seconds())

            if diff < min_diff:
                min_diff = diff
                closest_element = element

    return closest_element


def update_ongoing_issues(issue: Any, issue_work: Dict[str, List[Activity]], ongoing_issues: List[str]) -> None:
    works_by_issue = issue_work.get(issue.key)
    if works_by_issue:
        for work in works_by_issue:
            if work.start_time is None or work.end_time is None:
                update_end_time_for_ongoing_issues(issue, work, ongoing_issues)


def update_end_time_for_ongoing_issues(issue: Any, work: Activity, ongoing_issues: List[str]) -> None:
    if issue.key in ongoing_issues and work.end_time is None:
        print("Ongoing issue detected")
        work.end_time = datetime.now().replace(tzinfo=tz)


def process_issue_comments(issue: Issue, issue_work: Dict[str, List[Activity]]) -> None:
    for comment in issue.fields.comment.comments:
        if comment.author.accountId == config.JIRA_ACCOUNT_ID:
            created_time = datetime.strptime(comment.created, '%Y-%m-%dT%H:%M:%S.%f%z')
            works = issue_work.get(issue.key) or []
            works.append(Activity(
                id=issue.id,
                key=issue.key,
                type="Comment",
                start_time=created_time - timedelta(hours=2),
                end_time=created_time
            ))
            print(f"Comment - {comment.created} - Issue: {issue.key}")


def is_invite_accepted(event: Dict[str, Any]) -> bool:
    if event['status'] != 'confirmed':
        return False
    for att in event.get('attendees', []):
        if att['email'] == config.GCALENDAR_EMAIL and att['responseStatus'] == 'accepted':
            return True
    return False


def add_to_adjusted(adjusted_list: List[Activity], existing: Activity, start_time: datetime,
                    end_time: datetime) -> None:
    for adjusted in adjusted_list:
        if adjusted.start_time <= start_time < adjusted.end_time < end_time:
            start_time = adjusted.end_time
            return add_to_adjusted(adjusted_list, existing, start_time, end_time)
        elif start_time < adjusted.start_time < end_time <= adjusted.end_time:
            end_time = adjusted.start_time
            return add_to_adjusted(adjusted_list, existing, start_time, end_time)
        elif start_time < adjusted.start_time and adjusted.end_time < end_time:
            first_start_time = start_time
            first_end_time = adjusted.start_time
            add_to_adjusted(adjusted_list, existing, first_start_time, first_end_time)
            second_start_time = adjusted.end_time
            second_end_time = end_time
            return add_to_adjusted(adjusted_list, existing, second_start_time, second_end_time)
        elif adjusted.start_time <= start_time and adjusted.end_time >= end_time:
            return
        else:
            continue
    adjusted_list.append(Activity(
        id=existing.id,
        key=existing.key,
        type=existing.type,
        start_time=start_time,
        end_time=end_time
    ))
    return


def break_into_days(activity: Activity) -> List[Activity]:
    start_dt = activity.start_time
    end_dt = activity.end_time
    delta = end_dt - start_dt
    day_entries = []

    while delta.total_seconds() > 0:
        # Skip weekends and out of office days
        if start_dt.weekday() >= 5 or (activity.key == 'Out of office' and delta > timedelta(hours=8)):
            start_dt = datetime.combine((start_dt + timedelta(days=1)).date(), datetime.min.time(), tzinfo=timezone.utc)
            delta = end_dt - start_dt
            continue

        day_end = datetime.combine(start_dt.date(), datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        if end_dt < day_end:
            day_end = end_dt
        delta_for_day = day_end - start_dt

        if delta_for_day.total_seconds() > 0:
            new_entry = activity.copy()
            new_entry.start_time = start_dt
            new_entry.end_time = day_end
            day_entries.append(new_entry)
        start_dt = day_end
        delta = end_dt - start_dt

    return day_entries


def is_assigned(history: Any, direction: Literal['from', 'to']) -> bool:
    result = None
    for it in history.items:
        if it.field == 'assignee':
            if (direction == 'to' and it.to == config.JIRA_ACCOUNT_ID) or (
                    direction == 'from' and getattr(it, 'from') == config.JIRA_ACCOUNT_ID):
                return True
            else:
                result = False
    return result


def find_index_by_type(arr: List[Activity], type: str) -> int:
    for idx, x in enumerate(arr):
        if x.type == type:
            return idx
    return -1


def start_work(works: List[Activity], item: Any, history: Any, issue: Issue) -> None:
    work_idx = find_index_by_type(works, item.toString)
    history_creation_date = datetime.strptime(history.created, '%Y-%m-%dT%H:%M:%S.%f%z')
    if work_idx == -1:
        work = Activity(id=issue.id, key=issue.key, type=item.toString, start_time=history_creation_date)
        works.append(work)
    else:
        work = works[work_idx]
        if work.start_time is None or work.start_time > history_creation_date:
            work.start_time = history_creation_date
        works[work_idx] = work


def close_work(works: List[Activity], item: Any, history: Any, issue: Issue) -> None:
    work_idx = find_index_by_type(works, item.fromString)
    history_creation_date = datetime.strptime(history.created, '%Y-%m-%dT%H:%M:%S.%f%z')
    if work_idx == -1:
        work = Activity(id=issue.id, key=issue.key, type=item.fromString, end_time=history_creation_date)
        works.append(work)
    else:
        work = works[work_idx]
        if work.end_time is None or work.end_time < history_creation_date:
            work.end_time = history_creation_date
        works[work_idx] = work


def add_issue_work(issue_work: Dict[str, List[Activity]], issue: Issue, item: Any, history: Any, assigned_to_me: bool,
                   assigned_from_me: bool) -> None:
    started_work = item.toString in config.STARTED_WORK_STATES and item.fromString not in config.STARTED_WORK_STATES
    finished_work = item.toString in config.FINISHED_WORK_STATES and item.fromString in config.STARTED_WORK_STATES
    switch_work = item.toString in config.STARTED_WORK_STATES and item.fromString in config.STARTED_WORK_STATES

    works = issue_work.get(issue.key) or []
    if started_work:
        start_work(works, item, history, issue)
    elif finished_work:
        close_work(works, item, history, issue)
    elif switch_work:
        if assigned_to_me is True:
            start_work(works, item, history, issue)
        if assigned_from_me is True:
            close_work(works, item, history, issue)
        if assigned_to_me is None and assigned_from_me is None:
            start_work(works, item, history, issue)
            close_work(works, item, history, issue)
    issue_work[issue.key] = works


if __name__ == '__main__':
    fill_tempo()