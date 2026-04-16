class Database:
    def init(self):
        self.users = {}

    def create_user(self, name, email, password):
        if email in self.users:
            return False

        self.users[email] = {
            "name": name,
            "password": password
        }
        return True

    def get_user(self, email):
        return self.users.get(email)