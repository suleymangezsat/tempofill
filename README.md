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
2. **Install required packages**  (Skip this step if you plan to use Docker):
   ```bash
   pip install -r requirements.txt
   ```

### Docker Setup

1. **Build the Docker image**:
   
   Navigate to the project directory and run:
   ```bash
   docker build -t tempofill .
   ```

2. **Verify the Image**:
   
   Check that the image was created successfully:
   ```bash
   docker images
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
     - `meeting_issue_id`: Used to specify the ID of a Jira issue that represents collective or team activities such as planning sessions, group internal meetings, or any general team-related work. This ID is particularly useful for logging time against a common Jira issue that encapsulates various team interactions which may not be linked to a specific project task or individual issue.

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
     - `comment_duration_hours`: The fixed number of hours to allocate for each Jira comment activity. This setting is used to automatically log a consistent amount of time for commenting tasks in Jira. For example, if you generally spend about one hour on commenting or reviewing comments on a task, setting this value to `1` will log one hour for each comment activity.
    
3. **First Run**:
- Upon the first run of the application, you will be prompted to authenticate with Google Calendar. Follow the instructions to complete the authentication process. This will generate a `token.json` file in your project directory, storing your user credentials.

## Usage
### Running Without Docker

To run the application directly on your machine:

```bash
python main.py
```

### Running With Docker
   
Mount the **config.ini**, **credentials.json** and **token.json** files to use your configuration:
```bash
docker run -it --rm --name tempofill-app -v "$(pwd)/config.ini:/usr/src/app/config.ini" -v "$(pwd)/credentials.json:/usr/src/app/credentials.json" -v "$(pwd)/token.json:/usr/src/app/token.json" tempofill
```

## Contributing
Contributions to TempoFill are welcome! Feel free to report issues or submit pull requests.