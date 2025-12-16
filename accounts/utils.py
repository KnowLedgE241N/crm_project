def get_role(user) -> str | None:
    return getattr(user, "role", None)


def is_admin(user) -> bool:
    return user.is_superuser or get_role(user) == "ADMIN"


def is_manager(user) -> bool:
    return get_role(user) == "MANAGER"


def is_staff_role(user) -> bool:
    return get_role(user) == "STAFF"


def is_volunteer(user) -> bool:
    return get_role(user) == "VOLUNTEER"


def can_manage_forms(user) -> bool:
    """
    Forms are global for all non-volunteer users.
    """
    return user.is_authenticated and not is_volunteer(user)


def can_fill_forms(user) -> bool:
    """
    Everyone logged in can fill forms (including volunteers).
    """
    return user.is_authenticated


def can_access_tables(user) -> bool:
    """
    Volunteers cannot access the CRM tables UI.
    """
    return user.is_authenticated and not is_volunteer(user)


def can_view_all(user) -> bool:
    """
    Keep this for record-level visibility in CRM tables.
    Admin/Manager can view all records.
    """
    return is_admin(user) or is_manager(user)


def can_add_records(user) -> bool:
    """
    Keep your existing behaviour: who can manually add records in Tables UI.
    """
    return is_admin(user) or is_manager(user)


def can_manage_record(user, obj) -> bool:
    """
    Admin/Manager manage everything.
    Staff manage only their own created records (if supported).
    Volunteers cannot manage records.
    """
    if can_view_all(user):
        return True

    if is_staff_role(user) and hasattr(obj, "created_by_id"):
        return obj.created_by_id == user.id

    return False
