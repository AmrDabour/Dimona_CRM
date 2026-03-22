from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import settings
from app.core.redis import redis_client


class GoogleCalendarService:
    """Google Calendar integration service."""

    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ]

    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

    def get_auth_url(self, user_id: UUID) -> str:
        """Generate OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=str(user_id),
        )

        return auth_url

    async def exchange_code(self, code: str, user_id: UUID) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        flow.fetch_token(code=code)
        credentials = flow.credentials

        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes),
        }

        await redis_client.set_json(
            f"google_calendar:{user_id}",
            token_data,
            expire=86400 * 30,
        )

        return token_data

    async def get_credentials(self, user_id: UUID) -> Optional[Credentials]:
        """Get stored credentials for a user."""
        token_data = await redis_client.get_json(f"google_calendar:{user_id}")

        if not token_data:
            return None

        return Credentials(
            token=token_data["token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data.get("scopes"),
        )

    async def create_event(
        self,
        user_id: UUID,
        summary: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a calendar event."""
        credentials = await self.get_credentials(user_id)
        if not credentials:
            return None

        service = build("calendar", "v3", credentials=credentials)

        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        event = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all" if attendees else "none",
        ).execute()

        return created_event

    async def update_event(
        self,
        user_id: UUID,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a calendar event."""
        credentials = await self.get_credentials(user_id)
        if not credentials:
            return None

        service = build("calendar", "v3", credentials=credentials)

        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        if summary:
            event["summary"] = summary
        if start_time:
            event["start"]["dateTime"] = start_time.isoformat()
        if end_time:
            event["end"]["dateTime"] = end_time.isoformat()
        if description:
            event["description"] = description

        updated_event = service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event,
        ).execute()

        return updated_event

    async def delete_event(self, user_id: UUID, event_id: str) -> bool:
        """Delete a calendar event."""
        credentials = await self.get_credentials(user_id)
        if not credentials:
            return False

        service = build("calendar", "v3", credentials=credentials)

        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except Exception:
            return False

    async def list_events(
        self,
        user_id: UUID,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """List calendar events."""
        credentials = await self.get_credentials(user_id)
        if not credentials:
            return []

        service = build("calendar", "v3", credentials=credentials)

        if time_min is None:
            time_min = datetime.utcnow()
        if time_max is None:
            time_max = time_min + timedelta(days=30)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        return events_result.get("items", [])


calendar_service = GoogleCalendarService()
