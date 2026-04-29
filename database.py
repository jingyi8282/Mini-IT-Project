class Database:
    def init(self):
        self.users = {}   # email -> {name, password}
        self.tasks = {}   # email -> list of tasks

    # USER
    def create_user(self, name, email, password):
        if email in self.users:
            return False

        self.users[email] = {
            "name": name,
            "password": password
        }

        self.tasks[email] = []
        return True

    def get_user(self, email):
        return self.users.get(email)

    # TASK
    def add_task(self, email, title, priority, deadline, category):
        task_id = len(self.tasks[email]) + 1

        task = [task_id, email, title, priority, deadline, category]
        self.tasks[email].append(task)

    def get_user_tasks(self, email):
        return self.tasks.get(email, [])

    def delete_task(self, task_id, email):
        if email in self.tasks:
            self.tasks[email] = [
                t for t in self.tasks[email] if t[0] != task_id
            ]

    def update_task(self, task_id, email, title, priority, deadline):
        if email in self.tasks:
            for task in self.tasks[email]:
                if task[0] == task_id:
                    task[2] = title
                    task[3] = priority
                    task[4] = deadline