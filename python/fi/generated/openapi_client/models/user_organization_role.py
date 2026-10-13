from enum import Enum


class UserOrganizationRole(str, Enum):
    ADMIN = "Admin"
    MEMBER = "Member"
    OWNER = "Owner"
    VIEWER = "Viewer"
    WORKSPACE_ADMIN = "workspace_admin"
    WORKSPACE_MEMBER = "workspace_member"
    WORKSPACE_VIEWER = "workspace_viewer"

    def __str__(self) -> str:
        return str(self.value)
