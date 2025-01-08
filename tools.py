from utilities import get_all_mails, Uschedule_meeting, get_free_time_slots, send_mail_to_user, move_mail_to_folder
from datetime import datetime, timezone
from typing import Annotated, List, Optional


def iso_to_datetime(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00")).astimezone(timezone.utc)


def available_free_slots_for_meeting(for_date: Annotated[str, "ISO 8601 datetime string in UTC (e.g., '2024-12-23T00:00:00Z')"]) -> str:
    """
    Retrieves free time slots for a specific date.
    """
    return get_free_time_slots(for_date)




def read_mails() -> str:
    """Fetches all emails for processing."""
    return get_all_mails()




def schedule_meeting(
    subject: Annotated[str, "The subject or title of the meeting"],
    start_time: Annotated[str, "ISO 8601 datetime string for the start time in UTC (e.g., '2024-12-23T10:00:00Z')"],
    end_time: Annotated[str, "ISO 8601 datetime string for the end time in UTC (e.g., '2024-12-23T11:00:00Z')"],
    location: Annotated[str, "The location of the meeting (e.g., 'Online' or a physical address)"],
    attendees: Annotated[List[str], "A list of email addresses of attendees"]
) -> str:
    """
    Schedules a meeting and returns a success message.
    """
    # Convert ISO 8601 strings to datetime objects
    try:
        start_time = iso_to_datetime(start_time)
        end_time = iso_to_datetime(end_time)
    except ValueError as e:
        return f"Error parsing datetime: {e}"

    # Schedule the meeting using the Uschedule_meeting function
    result = Uschedule_meeting(subject, start_time, end_time, location, attendees)
    return result



def send_mail(
    recipient_email: Annotated[str, "The email address of the recipient"],
    email_subject: Annotated[str, "The subject of the email"],
    email_body: Annotated[str, "The body content of the email in HTML format"]
) -> str:
    """
    Sends an email to the recipient and returns success or error.
    """
    # Validate email format (basic check)
    if "@" not in recipient_email or "." not in recipient_email.split("@")[-1]:
        raise ValueError("Invalid email address format.")

    try:
        result = send_mail_to_user(recipient_email, email_subject, email_body)
    except Exception as e:
        return f"Error sending email: {e}"

    return f"Email sent successfully to {recipient_email}: {result}"



def move_email(
    message_id: Annotated[str, "The ID of the email message to be moved"]
) -> str:
    """
    Moves an email to a folder. Returns 'Success' or 'Failed'.
    """
    if not message_id:
        raise ValueError("The message_id cannot be empty.")

    # Call the helper function to move the email
    result = move_mail_to_folder(message_id)
    return result






