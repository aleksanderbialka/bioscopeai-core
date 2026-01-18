from bioscopeai_core.app.models import UserRole, UserStatus


class ServiceUser:
    """Pseudo-user object for service authentication."""

    def __init__(self, service_name: str) -> None:
        self.id = service_name
        self.role: UserRole = UserRole.SERVICE
        self.status: UserStatus = UserStatus.ACTIVE
        self.email = f"{service_name}@service.internal"
        self.username = service_name
        self.is_verified = True
        self.is_superuser = False

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_admin(self) -> bool:
        return False

    def has_role(self, required: UserRole) -> bool:
        """Service has access to everything."""
        return self.role.has_at_least(required)
