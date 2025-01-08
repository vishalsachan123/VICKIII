from autogen import ConversableAgent
from dotenv import load_dotenv
import os
from tools import available_free_slots_for_meeting,read_mails,schedule_meeting,send_mail,move_email

from typing import Dict,Union
from autogen.io.base import IOStream
from autogen.agentchat.agent import Agent
from autogen.formatting_utils import colored
from autogen.oai.client import OpenAIWrapper
from autogen.code_utils import content_str


# Load environment variables
load_dotenv()

# Define environment variable keys for API setup
model = os.getenv('model')
api_type = os.getenv('api_type')
api_key = os.getenv('api_key')
base_url = os.getenv('base_url')
api_version = os.getenv('api_version')

config_list = [{"model": model, "api_type": api_type, "api_key": api_key, "base_url": base_url, "api_version": api_version}]
llm_config = {"timeout": 600, "cache_seed": 42, "config_list": config_list, "temperature": 0}

def t(r,c):
    # print(f'R:{r}')
    # print(f'C:{c}')
    pass


class CustomConversableAgent(ConversableAgent):
    def __init__(self, name,system_message,llm_config,is_termination_msg, human_input_mode,max_consecutive_auto_reply):
        super().__init__(name=name,system_message=system_message, llm_config=llm_config,is_termination_msg=is_termination_msg,human_input_mode=human_input_mode,max_consecutive_auto_reply=max_consecutive_auto_reply)

    def _print_received_message(self, message: Union[Dict, str], sender: Agent):
        iostream = IOStream.get_default()
        
        # print the message received
        iostream.print(colored(sender.name, "yellow"), "(to", f"{self.name}):\n", flush=True)
        #add_e('assistant',f'{sender.name} (to {self.name}):\n')#101
        message = self._message_to_dict(message)

        if message.get("tool_responses"):  # Handle tool multi-call responses
            for tool_response in message["tool_responses"]:
                self._print_received_message(tool_response, sender)
            if message.get("role") == "tool":
                return  # If role is tool, then content is just a concatenation of all tool_responses

        if message.get("role") in ["function", "tool"]:
            if message["role"] == "function":
                id_key = "name"
            else:
                id_key = "tool_call_id"
            id = message.get(id_key, "No id found")
            func_print = f"***** Response from calling {message['role']} ({id}) *****"
            iostream.print(colored(func_print, "green"), flush=True)
            add_e('assistant',func_print)#101
            iostream.print(message["content"], flush=True)
            add_e('assistant',message["content"])#101
            iostream.print(colored("*" * len(func_print), "green"), flush=True)
            #add_e('assistant',"*" * len(func_print))#101

        else:
            content = message.get("content")
            if content is not None:
                if "context" in message:
                    content = OpenAIWrapper.instantiate(
                        content,
                        message["context"],
                        self.llm_config and self.llm_config.get("allow_format_str_template", False),
                    )
                iostream.print(content_str(content), flush=True)
                add_e('assistant',f'{content_str(content)}')#101
            if "function_call" in message and message["function_call"]:
                function_call = dict(message["function_call"])
                func_print = (
                    f"***** Suggested function call: {function_call.get('name', '(No function name found)')} *****"
                )
                iostream.print(colored(func_print, "green"), flush=True)
                add_e('assistant',func_print)#101
                iostream.print(
                    "Arguments: \n",
                    function_call.get("arguments", "(No arguments found)"),
                    flush=True,
                    sep="",
                )
                add_e('assistant',f'Arguments: \n{function_call.get("arguments", "(No arguments found)")}')#101
                iostream.print(colored("*" * len(func_print), "green"), flush=True)
                #add_e('assistant',"*" * len(func_print))#101
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:#111
                    id = tool_call.get("id", "No tool call id found")
                    function_call = dict(tool_call.get("function", {}))
                    func_print = f"***** Suggested tool call ({id}): {function_call.get('name', '(No function name found)')} *****"
                    iostream.print(colored(func_print, "green"), flush=True)
                    add_e('assistant',func_print)#101
                    iostream.print(
                        "Arguments: \n",
                        function_call.get("arguments", "(No arguments found)"),
                        flush=True,
                        sep="",
                    )
                    add_e('assistant',f'Arguments: \n{function_call.get("arguments", "(No arguments found)")}')#101
                    iostream.print(colored("*" * len(func_print), "green"), flush=True)
                    #add_e('assistant',"*" * len(func_print))#101

        iostream.print("\n", "-" * 80, flush=True, sep="")
        #add_e('assistant',"-" * 80)#101






# Define the Assistant Agent with improved system messages for clarity
assistant = CustomConversableAgent(
    name="Assistant",
    system_message = (
    "You are an intelligent meeting scheduling assistant and normal conversation assistant also. Your responsibilities include doing normal conversation and  handling multiple meeting requests efficiently. Your tasks are as follows:\n"
    "-> if user is doing normal conversation then do only normal conversation only and return TERMINATE e.g. Hii -> Hello   TERMINATE ,but if there is any tool call then do not include TERMINATE"
    "-> Do only what user say, do not schedule meeting untill user say to schedule"
    "the process for scheduling meeting is as follows: \n"
    "1. Read incoming emails from clients to identify meeting requests.\n"
    "2. For each meeting request, check the availability by calling the tool to retrieve free time slots for meetings on the requested date before scheduling any meeting.\n"
    "3. When selecting a free slot for scheduling, ensure that a buffer time (e.g., 15 minutes) is added between consecutive meetings. Avoid scheduling meetings directly after another meeting without accounting for this buffer period. Leverage busy slots.\n"
    "4. If a free slot is available just after a meeting ends, adjust the start time of the free slot by adding 15 minutes as a rest period before scheduling.\n"
    "5. Schedule the meeting based on the client's request, including the subject, start time, end time, location, and attendees. If the adjusted free slot (with buffer time) does not suffice, look for the next suitable free slot that accommodates the meeting duration.\n"
    "6. After scheduling the meeting, generate a meeting link (online).\n"
    "7. Insert the meeting link into the email body and send the email to all attendees.\n"
    "8. After each meeting is scheduled, move the corresponding email to the designated folder using the 'move_email' tool.\n"
    "9. If no new emails are found requesting meetings, return the message 'TERMINATE' to indicate that no action is needed.\n"
    "10. After successfully scheduling the meeting and notifying the clients, return 'TERMINATE' to signal the task is complete.\n"
    "11. In case of errors or issues, provide meaningful feedback to assist in resolving them.\n"
    "12. For multiple meeting requests, repeat the steps above for each request, ensuring each email is processed independently and moved to the folder after the meeting is scheduled.\n"
    "13. If no suitable free slot is found for a meeting request, do not schedule the meeting and do not move the email to the folder. Instead, return 'TERMINATE' to indicate that the task cannot be completed.\n"
    "Make sure that when choosing a suitable time for meetings:\n"
    "- The selected time respects the buffer period and allows for rest between meetings.\n"
    "- The rest period is implemented intelligently by adjusting the start time of available slots, ensuring that attendees have sufficient recovery time while maximizing efficient use of the schedule.\n"
    "- Meetings are only scheduled in slots that fully accommodate their duration after considering the buffer time.\n"
    "- After scheduling each meeting, move the email to the folder as requested, ensuring the entire process is handled for each individual request."
    ),
    llm_config=llm_config,
    
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    human_input_mode="NEVER",

    max_consecutive_auto_reply=7  # Prevent endless loop by limiting replies
)



user_proxy = CustomConversableAgent(
    name="User",
    system_message="You execute commands and provide responses back to the assistant.",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
    max_consecutive_auto_reply=7  # Limit consecutive auto-replies to 5
)


# Register tool functions
assistant.register_for_llm(name="read_mails", description="Read incoming emails from clients.")(read_mails)
assistant.register_for_llm(name="schedule_meeting", description="Tool for scheduling meetings.")(schedule_meeting)
assistant.register_for_llm(name="available_free_slots_for_meeting", description="check or get the availiability by free time slots for meetings on the requested date.")(available_free_slots_for_meeting)
assistant.register_for_llm(name="send_mail", description="Send an email to the client.")(send_mail)
assistant.register_for_llm(name="move_email", description="Move an email to the specified folder.")(move_email)

# Register execution functions for user proxy
user_proxy.register_for_execution(name="read_mails")(read_mails)
user_proxy.register_for_execution(name="send_mail")(send_mail)
user_proxy.register_for_execution(name="schedule_meeting")(schedule_meeting)
user_proxy.register_for_execution(name="available_free_slots_for_meeting")(available_free_slots_for_meeting)
user_proxy.register_for_execution(name="move_email")(move_email)

# Start the task to read client emails, schedule meetings, and notify the clients
# chat_result = user_proxy.initiate_chat(
#     assistant,
#    message=(
#         "Read client emails, find meeting requests, check free slots, and schedule meetings. "
#         "Notify the clients about the scheduled meetings. "
#         "Move the email to the specified folder after scheduling the meeting."
#     )
# )
add_e = t



def handle_query(user_input,add_entry):
    global add_e
    add_e = add_entry
    chat_result = user_proxy.initiate_chat(
    assistant,
    message=user_input,
    clear_history = False
    )





# chat_result = user_proxy.initiate_chat(
#     assistant,
#    message=(
#         "get my unread mails"
#     )
# )


# Get the cost of the chat.

#import pprint
#pprint.pprint(chat_result.cost)




#assistant.register_for_llm(name="get_free_slots_for_meeting", description="Get free time slots for scheduling a meeting on a particular day")(get_free_slots_for_meeting)


# assistant = ConversableAgent(
#     name="Assistant",
#     system_message = (
#     "You are an intelligent meeting scheduling assistant. Your responsibilities include the following tasks:\n"
#     "1. Read incoming emails from clients to identify meeting requests.\n"
#     "2. Check the availability of free time slots for meetings on the requested date.\n"
#     "3. When selecting a free slot for scheduling, ensure that a buffer time (e.g., 15 minutes) is added between consecutive meetings, avoiding scheduling just after another meeting to provide the attendees with enough rest. for doing this leverage the busy slots\n"
#     "4. Schedule the meeting based on the client's request, including the subject, start time, end time, location, and attendees.\n"
#     "5. After scheduling the meeting, generate a meeting link (if online) or confirm the meeting location.\n"
#     "6. Insert the meeting link into the email body and send the email to all attendees.\n"
#     "7. Ensure that the meeting link is correctly included and that the email is only sent after the meeting is scheduled.\n"
#     "8. If no new emails are found requesting meetings, return the message 'TERMINATE' to indicate that no action is needed.\n"
#     "9. After successfully scheduling the meeting and notifying the clients, return 'TERMINATE' to signal the task is complete.\n"
#     "You must ensure that the actions occur in this order, with no steps skipped.\n"
#     "In case of errors or issues, provide meaningful feedback to assist in resolving them.\n"
#     "Make sure that when choosing a suitable time for meetings, the selected time respects the buffer period and allows for rest between meetings."
#     ),
#     llm_config=llm_config,
#     max_consecutive_auto_reply=7  # Prevent endless loop by limiting replies 
# )





# assistant = ConversableAgent(
#     name="Assistant",
#     system_message=(
#         "You are an intelligent meeting scheduling assistant. Your responsibilities include the following tasks:\n"
#         "1. Read incoming emails from clients to identify meeting requests.\n"
#         "2. Check the availability of free time slots for meetings on the requested date.\n"
#         "3. Schedule the meeting based on the client's request, including the subject, start time, end time, location, and attendees.\n"
#         "4. After scheduling the meeting, generate a meeting link (if online) or confirm the meeting location.\n"
#         "5. Insert the meeting link into the email body and send the email to all attendees.\n"
#         "6. Ensure that the meeting link is correctly included and that the email is only sent after the meeting is scheduled.\n"
#         "7. If no new emails are found requesting meetings, return the message 'TERMINATE' to indicate that no action is needed.\n"
#         "8. After successfully scheduling the meeting and notifying the clients, return 'TERMINATE' to signal the task is complete.\n"
#         "9. When selecting a free slot for scheduling, ensure that a buffer time (e.g., 15 minutes) is added between consecutive meetings, avoiding scheduling just after another meeting.\n"

#         "You must ensure that the actions occur in this order, with no steps skipped.\n"
#         "In case of errors or issues, provide meaningful feedback to assist in resolving them."
#     ),  
#     llm_config=llm_config,
#     max_consecutive_auto_reply=7  # Prevent endless loop by limiting replies 
# )

# assistant = ConversableAgent(
#     name="Assistant",
#     system_message=(
#         "You are an intelligent meeting scheduling assistant. Your tasks include the following:\n"
#         "1. Reading incoming emails from clients to identify meeting requests.\n"
#         "2. Checking the availability of free time slots for meetings on the requested date.\n"
#         "3. Scheduling meetings based on client requests, including the subject, start time, end time, location, and attendees.\n"
#         "4. Sending email notifications to clients to confirm meeting details or inform them of scheduling changes.\n"
#         "You must complete each task efficiently using the available tools. Your objective is to ensure smooth scheduling and communication.\n"
#         "Once you have scheduled the meeting and notified the clients, return the message 'TERMINATE' to signal the task is complete.\n"
#         "In case of errors or issues, provide meaningful feedback to assist in resolving them."
#     ),
#     llm_config=llm_config,
#     max_consecutive_auto_reply=7  # Prevent endless loop by limiting replies
# )



# system_message = (
#     "You are an intelligent meeting scheduling assistant. Your responsibilities include the following tasks:\n"
#     "1. Read incoming emails from clients to identify meeting requests.\n"
#     "2. Check the availability of free time slots for meetings on the requested date.\n"
#     "3. Schedule the meeting based on the client's request, including the subject, start time, end time, location, and attendees.\n"
#     "4. After scheduling the meeting, generate a meeting link (if online) or confirm the meeting location.\n"
#     "5. Insert the meeting link into the email body and send the email to all attendees.\n"
#     "6. Ensure that the meeting link is correctly included and that the email is only sent after the meeting is scheduled.\n"
#     "7. If no new emails are found requesting meetings, return the message 'TERMINATE' to indicate that no action is needed.\n"
#     "8. After successfully scheduling the meeting and notifying the clients, return 'TERMINATE' to signal the task is complete.\n"
#     "9. When selecting a free slot for scheduling, ensure that a buffer time (e.g., 15 minutes) is added between consecutive meetings, avoiding scheduling just after another meeting.\n"
#     "You must ensure that the actions occur in this order, with no steps skipped.\n"
#     "In case of errors or issues, provide meaningful feedback to assist in resolving them."
# )


