class Database:
    def __init__(self):
        self.users = {}          # stores users: email -> {name, password}
        self.tasks = {}          # stores tasks: task_id -> task data
        self.next_task_id = 1    # auto-increment task ID

    # ============ USER FUNCTIONS ============
    
    def create_user(self, name, email, password):
        if email in self.users:
            return "Email already exists!"

        # save user
        self.users[email] = {
            "name": name,
            "password": password
        }
        return True

    def check_login(self, email, password):
        # check if user exists and password matches
        if email in self.users and self.users[email]["password"] == password:
            user_id = email  # Use email as ID
            user_name = self.users[email]["name"]
            return (user_id, user_name, email)
        return None

    def get_user(self, email):
        return self.users.get(email)

    # ============ TASK FUNCTIONS ============
    
    def add_task(self, user_id, title, priority, deadline, category):
        """Add a new task for a user"""
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
        """Get all tasks for a specific user"""
        user_tasks = []
        for task_id, task in self.tasks.items():
            if task["user_id"] == user_id:
                # Return as tuple to match expected format
                user_tasks.append((
                    task_id,           
                    task["user_id"],  
                    task["title"],    
                    task["priority"], 
                    task["deadline"],  
                    task["category"],  
                    task["completed"], 
                    None               
                ))
        return user_tasks

    def update_task_status(self, task_id, user_id, status):
        """Mark task as completed (1) or not completed (0)"""
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            self.tasks[task_id]["completed"] = status
            return True
        return False

    def delete_task(self, task_id, user_id):
        """Delete a task"""
        if task_id in self.tasks and self.tasks[task_id]["user_id"] == user_id:
            del self.tasks[task_id]
            return True
        return False