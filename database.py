class Database:
    def __init__(self):
        self.users = {}
        self.tasks = {}
        self.next_task_id = 1

    def create_user(self, name, email, password):
        if email in self.users: return False
        self.users[email] = {"name": name, "password": password}
        return True

    def check_login(self, email, password):
        if email in self.users and self.users[email]["password"] == password:
            return (email, self.users[email]["name"], email)
        return None

    def get_user_tasks(self, user_id):
        user_tasks = []
        for tid, t in self.tasks.items():
            if t.get("user_id") == user_id:
                user_tasks.append((tid, t["user_id"], t["title"], t["priority"], t["deadline"], t["category"], t["completed"]))
        return user_tasks

    def add_task(self, user_id, title, priority, deadline, category):
        tid = self.next_task_id
        self.tasks[tid] = {"user_id": user_id, "title": title, "priority": priority, "deadline": deadline, "category": category, "completed": 0}
        self.next_task_id += 1
        return tid

    def update_task(self, task_id, user_id, title, priority, deadline):
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            self.tasks[task_id].update({"title": title, "priority": priority, "deadline": deadline})
            return True
        return False

    def delete_task(self, task_id, user_id):
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            del self.tasks[task_id]
            return True
        return False