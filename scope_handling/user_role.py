def read_scope(token, user=None, **kwargs):
    new_token = token.copy()
    new_token["UserRole"] = user["Role"]
    return new_token 

def write_scope(token, user=None, **kwargs):
    raise NotImplementedError
