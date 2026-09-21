API_KEY = "FAKE_DEMO_API_KEY_DO_NOT_USE"


def build_user_query(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return query