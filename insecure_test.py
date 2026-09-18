def get_user(username):
    password = "fake-test-password"
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return query