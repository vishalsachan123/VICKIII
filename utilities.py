import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from access_token import get_access_token
import re
from datetime import datetime, timedelta, timezone

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>READ MAILS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def fetch_recent_unread_emails(access_token):
    top = 5
    # Define the API endpoint for the Inbox folder
    endpoint = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"

    # Graph API query parameters to filter unread emails and order by receivedDateTime descending
    query_params = {
        "$filter": "isRead eq false",
        "$orderby": "receivedDateTime desc",
        "$top": top  # Fetch up to 'top' emails (default is 50)
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    try:
        emails = []
        next_link = endpoint
        params = query_params.copy()

        while next_link:
            response = requests.get(next_link, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses
            data = response.json()
            emails.extend(data.get('value', []))
            
            # Check if there is a next page
            next_link = data.get('@odata.nextLink', None)
            params = None  # Parameters are only needed for the first request

            # Break if we've fetched the desired number of emails
            if len(emails) >= top:
                emails = emails[:top]
                break

        return {"value": emails}

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching emails: {e}")
        try:
            print(f"Response content: {response.content}")
        except NameError:
            print("No response content available.")
        return None


def extract_clean_text_from_html(body):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    
    # Remove all unwanted hidden elements
    for tag in soup.find_all(style=lambda value: value and 'display:none' in value):
        tag.decompose()
    
    # Get the text content and strip unnecessary whitespace
    clean_text = soup.get_text(separator="\n", strip=True)
    return clean_text


def get_all_mails():

    try:
        access_token = get_access_token()
        if not access_token:
            return "Failed to obtain access token."

        # Fetch recent unread emails
        emails = fetch_recent_unread_emails(access_token)
        if not emails:
            return "Failed to fetch unread emails."

        # Initialize the result string
        result = ''

        for email in emails.get("value", []):
            sender_address = email.get('from', {}).get('emailAddress', {}).get('address', 'No Address')

            # Exclude emails sent from Teams
            if "noreply@email.teams.microsoft.com" in sender_address:
                continue

            email_id = email.get('id', 'No ID')
            subject = email.get('subject', 'No Subject')
            sender = email.get('from', {}).get('emailAddress', {}).get('name', 'Unknown Sender')
            received_time = email.get('receivedDateTime', 'No Date')
            body = email.get('body', {}).get('content', 'No Body Content')
            
            # Get CC recipients
            cc_recipients = email.get('ccRecipients', [])
            cc_list = ', '.join([cc.get('emailAddress', {}).get('address', 'Unknown CC') for cc in cc_recipients]) or 'No CC Recipients'

            # Clean the HTML content of the email body
            clean_body = extract_clean_text_from_html(body)
            
            # Append email details to the result string
            result += f'''Subject: {subject}
ID: '{email_id}'
From: {sender} <{sender_address}>
Received: {received_time}
CC: {cc_list}
Body: {clean_body}
{"**********" * 10}
'''

        return result

    except Exception as e:
        return f"An error occurred: {e}"

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>READ MAILS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# def get_all_mails():
#     try:
#         access_token = get_access_token()
#         # Fetch unread emails from today
#         emails = fetch_today_unread_emails(access_token)
#         #print("Unread Emails Received Today are below")
#         temp = ''
#         for email in emails.get("value", []):
#             sender_address = email.get('from', {}).get('emailAddress', {}).get('address', 'No Address')

#             # Exclude emails sent from Teams
#             if "noreply@email.teams.microsoft.com" in sender_address:
#                 continue

#             email_id = email.get('id', 'No ID')
#             subject = email.get('subject', 'No Subject')
#             sender = email.get('from', {}).get('emailAddress', {}).get('name', 'Unknown Sender')
#             received_time = email.get('receivedDateTime', 'No Date')
#             body = email.get('body', {}).get('content', 'No Body Content')
            
#             # Get CC recipients
#             cc_recipients = email.get('ccRecipients', [])
#             cc_list = ', '.join([cc.get('emailAddress', {}).get('address', 'Unknown CC') for cc in cc_recipients]) or 'No CC Recipients'


#             # Clean the HTML content of the email body
#             clean_body = extract_clean_text_from_html(body)
            
#             # Print the details of the email

#             temp = temp + f'''Subject: {subject}
# ID: '{email_id}'
# From: {sender} <{sender_address}>
# Received: {received_time}
# CC: {cc_list}
# Body: {clean_body}
# {"-" * 40}
# '''
#         return temp

#     except Exception as e:
#         return f"An error occurred: {e}"

# def fetch_today_unread_emails(access_token):
#     """
#     Fetch unread emails received today using Microsoft Graph API.

#     Parameters:
#     - access_token: The access token for authenticating with Microsoft Graph API.

#     Returns:
#     - JSON response containing unread emails.
#     """
#     # Get today's start and end time in ISO 8601 format (UTC)
#     today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
#     today_end = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
    
#     # Graph API query parameters to filter unread emails
#     query_params = {
#         "$filter": f"isRead eq false and receivedDateTime ge {today_start} and receivedDateTime le {today_end}",
#         "$top": 50  # Fetch up to 50 emails (can be adjusted)
#     }

#     # Define the API endpoint
#     endpoint = "https://graph.microsoft.com/v1.0/me/messages"
#     headers = {"Authorization": f"Bearer {access_token}"}
    
#     try:
#         # Make the GET request to fetch emails
#         response = requests.get(endpoint, headers=headers, params=query_params)
#         response.raise_for_status()  # Raise HTTPError if response status is 4xx/5xx
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#         print(f"Response content: {response.content}")
#         return None

# def extract_clean_text_from_html(body):
#     # Parse the HTML using BeautifulSoup
#     soup = BeautifulSoup(body, "html.parser")
    
#     # Remove all unwanted hidden elements
#     for tag in soup.find_all(style=lambda value: value and 'display:none' in value):
#         tag.decompose()
    
#     # Get the text content and strip unnecessary whitespace
#     clean_text = soup.get_text(separator="\n", strip=True)
#     return clean_text

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Schedule Meetings>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def Uschedule_meeting(subject, start_time, end_time, location, attendees):
    access_token = get_access_token()
    meeting_details = schedule_meeting(access_token, subject, start_time, end_time, location, attendees)
    temp = f'''Meeting Scheduled Successfully!"
        Subject: {meeting_details['subject']}
        Join URL: {meeting_details['join_url']}
'''
    return temp

def schedule_meeting(access_token, subject, start_time, end_time, location, attendees):
    """Schedules a meeting using the Microsoft Graph API."""
    url = "https://graph.microsoft.com/v1.0/me/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    attendees_list = [{"emailAddress": {"address": email}, "type": "required"} for email in attendees]

    meeting_data = {
        "subject": subject,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC"
        },
        "location": {
            "displayName": location
        },
        "allowNewTimeProposals": True,
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness",
        "attendees": attendees_list
    }

    response = requests.post(url, headers=headers, json=meeting_data)

    if response.status_code == 201:
        meeting = response.json()
        join_url = meeting.get("onlineMeeting", {}).get("joinUrl", "")
        return {
            "id": meeting.get("id"),
            "subject": meeting.get("subject"),
            "join_url": join_url
        }
    else:
        raise Exception(f"Error creating meeting: {response.text}")

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>get free time slots for  Meetings>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def get_free_time_slots(for_date):
    for_date = datetime.fromisoformat(for_date.replace("Z", "+00:00")).astimezone(timezone.utc)

    day = for_date
    access_token = get_access_token()
    events = get_calendar_events_from_today(access_token)
    busy_slots = find_busy_slots(events)

    free_slots = find_free_time_for_day(busy_slots, day)

    # Format the busy and free slots into a readable string
    formatted_busy_slots = "Busy Slots:\n" + "\n".join([f"From {start.strftime('%Y-%m-%d %H:%M:%S')} to {end.strftime('%Y-%m-%d %H:%M:%S')}" for start, end in busy_slots])
    formatted_free_slots = "Free Slots:\n" + "\n".join([f"From {start.strftime('%Y-%m-%d %H:%M:%S')} to {end.strftime('%Y-%m-%d %H:%M:%S')}" for start, end in free_slots])

    # Combine both the busy and free slots into a single response
    combined_slots = f"{formatted_busy_slots}\n\n{formatted_free_slots}"

    return combined_slots

def get_calendar_events_from_today(access_token):
    url = "https://graph.microsoft.com/v1.0/me/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get today's date in ISO 8601 format starting from midnight
    today_start = datetime.now(timezone.utc).date().isoformat() + "T00:00:00Z"

    # Define parameters to fetch events from today onwards
    params = {
        "$select": "subject,start,end",
        "$orderby": "start/dateTime",
        "$filter": f"start/dateTime ge '{today_start}'"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()["value"]
    else:
        raise Exception(f"Error fetching events: {response.text}")
    
# Function to find busy slots

def find_busy_slots(events):  
    busy_slots = []
    
    for event in events:
        try:
            # Remove excessive fractional seconds
            start_time_str = re.sub(r'\.\d+', '', event["start"]["dateTime"]).replace("Z", "+00:00")
            end_time_str = re.sub(r'\.\d+', '', event["end"]["dateTime"]).replace("Z", "+00:00")

            # Parse directly into offset-aware datetime objects with UTC timezone
            start_time = datetime.fromisoformat(start_time_str).replace(tzinfo=timezone.utc)
            end_time = datetime.fromisoformat(end_time_str).replace(tzinfo=timezone.utc)

            # Append to busy times
            busy_slots.append((start_time, end_time))
        except Exception as e:
            print(f"Skipping invalid event due to error: {e}. Event details: {event}")

    busy_slots.sort()
    return busy_slots

def find_free_time_for_day(busy_slots, day):
    # Define working hours
    work_start = day.replace(hour=3, minute=30, second=0, microsecond=0, tzinfo=timezone.utc)
    work_end = day.replace(hour=11, minute=30, second=0, microsecond=0, tzinfo=timezone.utc)

    # Get current time in UTC
    now = datetime.now(timezone.utc)

    # Check if the day has already passed
    if day.date() < now.date():
        return []  # Return an empty list for past days

    # Determine the start time for free slot calculation
    if day.date() == now.date():
        # If the day is today, start from the next rounded quarter-hour but not before work_start
        rounded_minutes = (now.minute // 15 + 1) * 15
        current_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=rounded_minutes)
        current_start = max(current_start, work_start)


    else:
        # Otherwise, start from the beginning of working hours
        current_start = work_start

    # Ensure the start time does not exceed working hours end
    if current_start >= work_end:
        return []  # No free time available

    # Sort busy slots by their start times
    busy_slots.sort()

    # Initialize the free slots list
    free_slots = []

    # Assumed duration and increment
    assumed_duration = timedelta(minutes=45)  # 45 minutes assumed duration
    increment_duration = timedelta(minutes=15)  # Increment assumed time by 15 minutes

    while current_start < work_end:
        assumed_end = current_start + assumed_duration

        # Check for interference with busy slots
        interference = False
        for busy_start, busy_end in busy_slots:
            if (busy_start < assumed_end and current_start < busy_end):
                # Interference detected
                interference = True
                current_start = max(current_start, busy_end)  # Move start to the end of this busy slot
                break

        if not interference:
            # No interference, add the assumed slot to free slots
            if assumed_end <= work_end:
                free_slots.append((current_start, assumed_end))
            current_start += increment_duration  # Move to the next assumed slot

    return free_slots

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>send mail to a user>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def send_mail_to_user(recipient_email, email_subject, email_body):
    access_token = get_access_token()
    return send_email(access_token, recipient_email, email_subject, email_body)

def send_email(access_token, to_email, subject, body_content):
    endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    email_payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }

    response = requests.post(endpoint, headers=headers, json=email_payload)

    if response.status_code == 202:
        return f"Email sent successfully to {to_email}."
    else:
        return f"Failed to send email. Status code: {response.status_code}, Response: {response.json()}"




#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>moving mail to A defined Folder>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def move_mail_to_folder(message_id):
    BASE_URL = "https://graph.microsoft.com/v1.0"
    ACCESS_TOKEN = get_access_token()
    TARGET_FOLDER_ID = 'AAMkAGRmOWJmNjk4LTI4NmEtNDYyNi1iOTVhLTEyOGFkNmZlODRmYwAuAAAAAABlqIKcBI6rTpjYHjKLwxvmAQDh6tmZQaL4Qazw_awSKB57AABb1FnsAAA='
    url = f"{BASE_URL}/me/messages/{message_id}/move"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "destinationId": TARGET_FOLDER_ID
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an HTTPError for non-2xx responses
        if response.status_code == 201:
            return "Successfully moved the mail to a folder."
    except requests.exceptions.RequestException:
        return "Failed to move mail."

    return "Failed to move mail."



