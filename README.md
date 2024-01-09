# TempoFill

## Introduction
TempoFill is an automation tool designed to streamline the process of logging work hours in Tempo. It automatically creates worklogs based on user activities in Jira and Google Calendar, simplifying time tracking and improving productivity.

## Features
- **Automated Worklog Entries**: Automatically fills Tempo worklogs based on Jira movements and Google Calendar activities.
- **Jira Integration**: Tracks issue status changes and time spent on different tasks in Jira.
- **Google Calendar Sync**: Logs time spent in meetings or events scheduled in Google Calendar.
- **Customizable Work Schedules**: Configurable work hours to match individual or team schedules.
- **Easy Configuration**: Simple setup with `config.ini` to manage user-specific settings.

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/suleymangezsat/TempoFill.git
   ```
2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```
   
## Configuration
Before running TempoFill, you need to set up your configuration:

1. **Google Calendar Authentication**:
- Visit the [Google Developers Console](https://console.cloud.google.com/project).
- Create a new project and enable the Google Calendar API for it.
- Create credentials for the OAuth 2.0 client IDs. Download the JSON file and rename it to `credentials.json`.
- Place `credentials.json` in the project's root directory.

2. **Setting up `config.ini`**:
   - Rename `example.config.ini` to `config.ini`.
   - Update the `config.ini` file with your specific settings:

     ### [run]
     - `start_date`: The start date for tracking activities (format: YYYY-MM-DD).
     - `end_date`: The end date for tracking activities (format: YYYY-MM-DD).
     - `timezone`: Your local timezone (e.g., `Etc/GMT-3`).

     ### [jira]
     - `account_id`: Your Jira account ID.
     - `project`: The key of the Jira project you are tracking.
     - `server`: The URL of your Jira server.
     - `username`: Your Jira username (usually your email).
     - `api_key`: Your Jira API key for authentication.

     ### [gcalendar]
     - `email`: The email address associated with your Google Calendar.

     ### [tempo]
     - `api_key`: The API key for accessing Tempo services.

     ### [work_states]
     - `started_work_states`: Comma-separated list of Jira states indicating the start of work.
     - `finished_work_states`: Comma-separated list of Jira states indicating the completion of work.
     - `priority_order`: Comma-separated list indicating the priority of activities (used when organizing activities).

     ### [work_schedule]
     - `workday_start_hour`: The hour at which your workday typically starts (e.g., `9` for 9 AM).
     - `workday_duration_hours`: The typical duration of your workday in hours (e.g., `8` for 8 hours).

    
3. **First Run**:
- Upon the first run of the application, you will be prompted to authenticate with Google Calendar. Follow the instructions to complete the authentication process. This will generate a `token.json` file in your project directory, storing your user credentials.

## Usage
To run the application:
   ```bash
   python main.py
   ```

## Contributing
Contributions to TempoFill are welcome! Feel free to report issues or submit pull requests.