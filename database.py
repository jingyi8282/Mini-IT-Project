import json
import os

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.tasks_file = "tasks.json"
        self.load_data()

    def load_data(self):
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

    def save_users(self):
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=2)

    def save_tasks(self):
        with open(self.tasks_file, "w") as f:
            json.dump(self.tasks, f, indent=2)

    # USER
    def create_user(self, name, email, password):
        if email in self.users:
            return False
        self.users[email] = {"name": name, "password": password}
        self.tasks[email] = []
        self.save_users()
        self.save_tasks()
        return True

    def check_login(self, email, password):
        if email in self.users and self.users[email]["password"] == password:
            return (email, self.users[email]["name"], email)
        return None

    def reset_password(self, email, new_password):
        if email not in self.users:
            return False
        self.users[email]["password"] = new_password
        self.save_users()
        return True

    # TASKS
    def add_task(self, email, title, priority, deadline, category):
        tasks = self.tasks.get(email, [])
        
        task_id = 1
        for task in tasks:
            if task["id"] >= task_id:
                task_id = task["id"] + 1
        
        new_task = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "deadline": deadline,
            "category": category,
            "status": "my_task"
        }
        
        if email not in self.tasks:
            self.tasks[email] = []
        
        self.tasks[email].append(new_task)
        self.save_tasks()
        return task_id

    def get_tasks(self, email):
        return self.tasks.get(email, [])

    def delete_task(self, email, task_id):
        if email in self.tasks:
            new_list = []
            for task in self.tasks[email]:
                if task["id"] != task_id:
                    new_list.append(task)
            self.tasks[email] = new_list
            self.save_tasks()

    def update_task(self, email, task_id, title, priority, deadline, category):
        if email in self.tasks:
            for task in self.tasks[email]:
                if task["id"] == task_id:
                    task["title"] = title
                    task["priority"] = priority
                    task["deadline"] = deadline
                    task["category"] = category
                    self.save_tasks()
                    return True
        return False

    def update_task_status(self, email, task_id, status):
        if email in self.tasks:
            for task in self.tasks[email]:
                if task["id"] == task_id:
                    task["status"] = status
                    self.save_tasks()
                    return True
        return False

    def get_tasks_by_status(self, email, status):
        tasks = self.tasks.get(email, [])
        return [t for t in tasks if t.get("status") == status]