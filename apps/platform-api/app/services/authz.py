from app.schemas.auth import UserRole


def ensure_role(current_role: UserRole, allowed_roles: list[UserRole]) -> None:
    if current_role not in allowed_roles:
        raise PermissionError('Insufficient permissions for this action')
