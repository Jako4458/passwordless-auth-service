import scope_handling.username
import scope_handling.email
import scope_handling.user_role

scope_handlers = {
    "read:username": username.read_scope,
    "read:email": email.read_scope,
    "read:user-role": user_role.read_scope,
}
