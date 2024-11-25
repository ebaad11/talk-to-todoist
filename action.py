# action.py

class Action:
    def __init__(self, action_type, task_id=None, content=None, due_string=None, due_lang=None, original_content=None, original_due_string=None):
        self.action_type = action_type
        self.task_id = task_id
        self.content = content
        self.due_string = due_string
        self.due_lang = due_lang
        self.preliminary_task = None  # For tracking tasks created during preview
        self.original_content = original_content  # Store original content
        self.original_due_string = original_due_string  # Store original due date

    def perform_preview(self, todoist_api):
        try:
            if self.action_type == 'create':
                print(f"Preview: Creating task '{self.content}' with due '{self.due_string}'")
                if not self.due_string:
                    warning = " ⚠️ Warning: No due date specified"
                    self.due_string = "today"
                else:
                    warning = ""
                
                self.preliminary_task = todoist_api.add_task(
                    content=f"{self.content} {warning} (🎉 created, awaiting confirmation)",
                    due_string=self.due_string,
                    due_lang=self.due_lang,
                )
            elif self.action_type == 'update':
                print(f"Preview: Updating task ID {self.task_id} to '{self.content}' with due '{self.due_string}'")
                if not self.original_content:
                    task = todoist_api.get_task(task_id=self.task_id)
                    self.original_content = task.content
                    self.original_due_string = task.due.string if task.due else None
                if self.content != self.original_content and self.due_string != self.original_due_string:
                    content = f"{self.content} (🛠️ modified, from {self.original_content} and due date from {self.original_due_string}, awaiting confirmation)"
                elif self.content != self.original_content:
                    content = f"{self.content} (🛠️ modified, from {self.original_content}, awaiting confirmation)"
                elif self.due_string != self.original_due_string:
                    content = f"{self.content} (🛠️ due date modified, from {self.original_due_string}, awaiting confirmation)"
                else:
                    content = f"{self.content} (awaiting confirmation)"
                todoist_api.update_task(
                    task_id=self.task_id,
                    content=content,
                    due_string=self.due_string,
                    due_lang=self.due_lang,
                )

            elif self.action_type == 'close':
                print(f"Preview: Marking task ID {self.task_id} {self.content} as 'will be closed'")
                if not self.original_content:
                    task = todoist_api.get_task(task_id=self.task_id)
                    self.original_content = task.content
                    self.original_due_string = task.due.string if task.due else None
                # Update the task content to indicate it will be closed
                todoist_api.update_task(
                    task_id=self.task_id,
                    content=f"~~{self.content}~~ ( ❌, awaiting confirmation)",
                    due_string=self.due_string,
                    due_lang=self.due_lang,
                )
            else:
                print(f"Preview: Unknown action type '{self.action_type}', ERROR")
        except Exception as e:
            print(f"An error occurred during preview: {e}")

    def perform_final(self, todoist_api):
        try:
            if self.action_type == 'create':
                print(f"Finalizing: Creating task '{self.content}' with due '{self.due_string}'")
                # Finalize task creation
                todoist_api.update_task(
                    task_id=self.preliminary_task.id,
                    content=self.content,
                    due_string=self.due_string,
                    due_lang=self.due_lang,
                )
            elif self.action_type == 'update':
                print(f"Finalizing: Updating task ID {self.task_id} to '{self.content}' with due '{self.due_string}'")
                # Finalize task update
                todoist_api.update_task(
                    task_id=self.task_id,
                    content=self.content,
                    due_string=self.due_string,
                    due_lang=self.due_lang,
                )
            elif self.action_type == 'close':
                print(f"Finalizing: Closing task ID {self.task_id} {self.content}")
                todoist_api.close_task(task_id=self.task_id)
            else:
                print(f"Finalizing: Unknown action type '{self.action_type}'")
        except Exception as e:
            error_message = f"An error occurred during finalization: {e}"
            task_info = f"Task ID: {self.task_id}, Action Type: {self.action_type}, Content: {self.content}, Due String: {self.due_string}, Due Lang: {self.due_lang}"
            print(error_message)
            print(f"Task Information: {task_info}")
            # Here you could also log to a file or a logging system if needed

    def revert_preview(self, todoist_api):
        try:
            if self.action_type == 'create':
                print(f"Reverting: Deleting preliminary task '{self.content}'")
                todoist_api.delete_task(task_id=self.preliminary_task.id)
            elif self.action_type == 'update':
                print(f"Reverting: Restoring original content and due date for task ID {self.task_id}")
                todoist_api.update_task(
                    task_id=self.task_id,
                    content=self.original_content,
                    due_string=self.original_due_string,
                    due_lang=self.due_lang,
                )
            elif self.action_type == 'close':
                print(f"Reverting: Restoring original content and due date for task ID {self.task_id}")
                todoist_api.update_task(
                    task_id=self.task_id,
                    content=self.original_content,
                    due_string=self.original_due_string,
                    due_lang=self.due_lang,
                )
            else:
                print(f"Reverting: Unknown action type '{self.action_type}'")
        except Exception as e:
            print(f"An error occurred during revert: {e}")