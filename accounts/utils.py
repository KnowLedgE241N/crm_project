def can_view_all(user) -> bool:
    return user.is_superuser or getattr(user, "role", None) in ("ADMIN", "MANAGER")

def can_add_records(user) -> bool:
    return user.is_superuser or getattr(user, "role", None) in ("ADMIN", "MANAGER")

def can_manage_record(user, obj) -> bool:
    # Admin/Manager can manage everything
    if user.is_superuser or getattr(user, "role", None) in ("ADMIN", "MANAGER"):
        return True

    # Staff can only manage objects they created (if model supports it)
    if hasattr(obj, "created_by_id"):
        return obj.created_by_id == user.id

    return False
