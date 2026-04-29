class Database:
    def init(self):
        self.users = {}
        self.tasks = {}
        self.next_task_id = 1

    # USER
    
    def create_user(self, name, email, password):
        if email in self.users:
            return False  
        
        self.users[email] = {"name": name, "password": password}
        return True

    def check_login(self, email, password):
        if email in self.users and self.users[email]["password"] == password:
            return (email, self.users[email]["name"], email)
        return None

    # TASKSS
    
    def add_task(self, user_id, title, priority, deadline, category):
        task_id = self.next_task_id
        self.next_task_id += 1
        self.tasks[task_id] = {
            "user_id": user_id,
            "title": title,
            "priority": priority,
            "deadline": deadline,
            "category": category,
            "completed": 0
        }
        return task_id

    def get_user_tasks(self, user_id):
        user_tasks = []
        for task_id, task in self.tasks.items():
            if task["user_id"] == user_id:
                user_tasks.append((
                    task_id, 
                    task["user_id"], 
                    task["title"],
                    task["priority"], 
                    task["deadline"], 
                    task["category"],
                    task["completed"]
                ))
        return user_tasks

    def delete_task(self, task_id, user_id):
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            del self.tasks[task_id]
            return True
        return False

    def update_task(self, task_id, user_id, title, priority, deadline):
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            self.tasks[task_id]["title"] = title
            self.tasks[task_id]["priority"] = priority
            self.tasks[task_id]["deadline"] = deadline
            return True
        return False