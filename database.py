class Database:
    def init(self):
        self.users = {}  # stores users: email -> {name, password}
    
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