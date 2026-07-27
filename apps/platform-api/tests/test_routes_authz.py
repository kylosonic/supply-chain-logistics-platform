from app.schemas.auth import UserRole
from app.services.authz import ensure_role


def test_admin_can_access_admin_endpoint():
    ensure_role(UserRole.ADMIN, [UserRole.ADMIN])


def test_operator_can_access_operator_endpoint():
    ensure_role(UserRole.OPERATOR, [UserRole.OPERATOR, UserRole.ADMIN])


def test_viewer_cannot_access_operator_endpoint():
    try:
        ensure_role(UserRole.VIEWER, [UserRole.OPERATOR, UserRole.ADMIN])
    except PermissionError:
        assert True
        return
    assert False, 'Expected PermissionError for viewer on operator role gate'
