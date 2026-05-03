import json
import os

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.tasks_file = "tasks.json"

        if os.path.exists(self.users_file):
            with open(self.users_file, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}

        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, "r") as f:
                self.tasks = json.load(f)
        else:
            self.tasks = {}

        self.next_id = 1
        for email in self.tasks:
            for task in self.tasks[email]:
                if task["id"] >= self.next_id:
                    self.next_id = task["id"] + 1

    def save_users(self):
        with open(self.users_file, "w") as f:
            json.dump(self.users, f)

    def save_tasks(self):
        with open(self.tasks_file, "w") as f:
            json.dump(self.tasks, f)

    def create_user(self, username, email, password):
        if email in self.users:
            return False
        self.users[email] = {"username": username, "password": password}
        self.tasks[email] = []
        self.save_users()
        self.save_tasks()
        return True

    def check_login(self, email, password):
        if email in self.users and self.users[email]["password"] == password:
            return (email, self.users[email]["username"], email)
        return None

    def add_task(self, email, title, priority, deadline):
        task = {"id": self.next_id, "title": title, "priority": priority, "deadline": deadline}
        self.tasks[email].append(task)
        self.next_id += 1
        self.save_tasks()
        return task["id"]

    def get_tasks(self, email):
        return self.tasks.get(email, [])

    def delete_task(self, email, task_id):
        new_list = [t for t in self.tasks[email] if t["id"] != task_id]
        self.tasks[email] = new_list
        self.save_tasks()

    def update_task(self, email, task_id, title, priority, deadline):
        for task in self.tasks[email]:
            if task["id"] == task_id:
                task["title"] = title
                task["priority"] = priority
                task["deadline"] = deadline
                self.save_tasks()
                return True
        return False