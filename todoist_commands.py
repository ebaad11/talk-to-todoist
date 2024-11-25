# todoist_assistant.py

from openai import OpenAI
from todoist_api_python.api import TodoistAPI
import json
import re
from datetime import datetime
from action import Action
import requests
import base64

class TodoistAssistant:
    def __init__(self, todoist_api_key):
        self.todoist_api = TodoistAPI(todoist_api_key)
        self.tasks = []
        # Initialize variables for logging
        self.log_worker_url = 'https://todoist-log-kv.ebaadforrandomstuff.workers.dev/'
        self.user_input = ''
        self.task_list = ''
        self.json_response = ''
        self.action_status = ''
        self.user_feedback = ''
        

    def get_tasks(self, filter="tomorrow"):
        try:
            self.tasks = self.todoist_api.get_tasks(filter=filter)
            print("\n" + "="*50)
            print(f"🌟 Here are your tasks for {filter}: 🌟")
            print("="*50 + "\n")
            for task in self.tasks:
                due_string = task.due.string if task.due else "No due date"
                print(f"Task: {task.content}\nDue Date: {due_string}\n" + "-"*50)
        except Exception as error:
            print(f"Error fetching tasks: {error}")
            self.tasks = []

    def get_task_content_by_id(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task.content
        return None

    def extract_json_from_message(self, message):
        pattern = r'```(?:json)?\n(.*?)\n```'
        match = re.search(pattern, message, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return message

    def parse_user_input(self, user_input):
        tasks_string = ""
        for task in self.tasks:
            tasks_string += f"Task ID: {task.id}, Content: '{task.content}'\n"
        self.task_list = tasks_string  # Store task list for logging

        # Obtain today's date
        WORKER_URL = "https://open-ai-logic-for-todolist-objects.ebaadforrandomstuff.workers.dev/"
        result = self.send_inputs(user_input,tasks_string,WORKER_URL)
        if result:
            content=result.get("AIResponse")
          
        json_text = self.extract_json_from_message(content)
        self.json_response = json_text  # Store JSON response for logging
        try:
            actions = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Assistant message:")
            actions = []
        # Format and print the actions nicely
        
        action_objects = []
        for action_data in actions:
            action_type = action_data.get('action')
            task_id = action_data.get('task_id')
            content = action_data.get('content')
            due_string = action_data.get('due_string')
            due_lang = action_data.get('due_lang')

            original_content = None
            original_due_string = None

            if action_type in ['update', 'close'] and task_id:
                # Get original task details
                task = self.todoist_api.get_task(task_id=task_id)
                original_content = task.content
                original_due_string = task.due.string if task.due else None

            action_obj = Action(
                action_type=action_type,
                task_id=task_id,
                content=content,
                due_string=due_string,
                due_lang=due_lang,
                original_content=original_content,
                original_due_string=original_due_string,
            )
            action_objects.append(action_obj)

        return action_objects

    def perform_actions(self, actions):
        # Preview phase
        for action in actions:
            action.perform_preview(self.todoist_api)

        # Display tasks for confirmation
        confirmation = input("Do you want to confirm these actions? (y/n): ")
        if confirmation.lower() == 'y':
            # Final execution phase
            self.action_status = 'confirmed'
            self.user_feedback = ''
            for action in actions:
                action.perform_final(self.todoist_api)
            print("Actions have been confirmed and executed.")
        else:
            # Optionally revert preliminary actions
            for action in actions:
                action.revert_preview(self.todoist_api)
            print("Actions have been canceled.")
            self.action_status = 'canceled'
            # Prompt for optional feedback
            feedback = input("If you want, please tell us what went wrong (we will send this to our server so we can improve the service):")
            self.user_feedback = feedback

   

    def run(self, user_input):
        self.user_input = user_input  # Store user input for logging
        actions = self.parse_user_input(user_input)
        
        self.perform_actions(actions)
        # Send the log after performing actions
        if self.action_status == "canceled":
            self.send_log()
    
    def send_inputs(self, user_input, task_string,WORKER_URL):
        # Prepare the payload
        payload = {
            'UserInput': user_input,
            'TaskString': task_string
        }

        try:
            # Send the POST request
            response = requests.post(WORKER_URL, json=payload)

            # Raise an exception for HTTP error codes
            response.raise_for_status()

            # Parse and return the JSON response
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f'An error occurred: {e}')
            return None
    def send_log(self):
        # Prepare the data to send
        data = {
            'user_input': self.user_input,
            'task_list': self.task_list,
            'json_response': self.json_response,
            'action_status': self.action_status,
            'user_feedback': self.user_feedback,
            'promt_version': "0.1" 
        }

        try:
            # Send the POST request to the log worker URL
            response = requests.post(self.log_worker_url, json=data)
            response.raise_for_status()
            print("Log data sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while sending log data: {e}")


if __name__ == "__main__":
    # Initialize with your API keys
    todoist_api_key = "25dacf3f0f704391fe08a04fdba996ffcd657f8d"  # Replace with actual Todoist API key
    
    
    # Create assistant instance
    assistant = TodoistAssistant(todoist_api_key)
    
    # Get tasks for tomorrow as an example
    # filter_query = "overdue | today"
    # filter_query = "today | tomorrow"
    filter_query = "today | 7 days"
    # filter_query = "today"
    assistant.get_tasks(filter_query)
 
    # add your filter queries here common queries are 
    
    # # Example user input
    user_input = input("What would you like to do with your tasks? ")
    
    # # Run the assistant with user input
    assistant.run(user_input)