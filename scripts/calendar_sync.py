#!/usr/bin/env python3
"""
calendar_sync.py - Google Calendar の予定を同期
環境変数: GOOGLE_CREDENTIALS_PATH
"""

import os
import sys
from datetime import datetime, timedelta

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Google API未インストール: pip install google-api-python-client google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context", "calendar")


def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def sync_calendar():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"認証ファイルが見つかりません: {CREDENTIALS_PATH}")
        return

    service = get_calendar_service()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    time_min = today.isoformat() + "Z"
    time_max = (today + timedelta(days=7)).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    # 日別にファイル出力
    for day_offset in range(7):
        date = today + timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")
        day_events = [
            e for e in events
            if e["start"].get("dateTime", e["start"].get("date", "")).startswith(date_str)
        ]

        output_file = os.path.join(OUTPUT_DIR, f"schedule_{date_str}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# スケジュール: {date_str}\n\n")
            if not day_events:
                f.write("予定なし\n")
            else:
                for event in day_events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    summary = event.get("summary", "（タイトルなし）")
                    attendees = event.get("attendees", [])
                    attendee_names = ", ".join(
                        a.get("displayName", a.get("email", "")) for a in attendees
                    )
                    f.write(f"- **{start}** {summary}\n")
                    if attendee_names:
                        f.write(f"  - 参加者: {attendee_names}\n")
                    f.write("\n")

    print(f"✅ Calendar同期完了: {len(events)}件（7日分）")


if __name__ == "__main__":
    sync_calendar()
