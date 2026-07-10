from __future__ import annotations

from enum import IntEnum, auto

from src.database.models import UserRole


class Permission(IntEnum):
    VIEW_ANALYTICS = auto()
    MANAGE_SETTINGS = auto()
    MANAGE_ROLES = auto()
    BAN_USERS = auto()
    KICK_USERS = auto()
    MUTE_USERS = auto()
    WARN_USERS = auto()
    DELETE_MESSAGES = auto()
    PIN_MESSAGES = auto()
    MANAGE_KNOWLEDGE = auto()
    MANAGE_FILTERS = auto()
    MANAGE_JOBS = auto()
    VIEW_LOGS = auto()
    ECONOMY_ADMIN = auto()
    GAMES_ADMIN = auto()
    SEND_ANNOUNCEMENTS = auto()


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.OWNER: set(Permission),
    UserRole.MANAGER: {
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_SETTINGS,
        Permission.MANAGE_ROLES,
        Permission.BAN_USERS,
        Permission.KICK_USERS,
        Permission.MUTE_USERS,
        Permission.WARN_USERS,
        Permission.DELETE_MESSAGES,
        Permission.PIN_MESSAGES,
        Permission.MANAGE_KNOWLEDGE,
        Permission.MANAGE_FILTERS,
        Permission.MANAGE_JOBS,
        Permission.VIEW_LOGS,
        Permission.ECONOMY_ADMIN,
        Permission.GAMES_ADMIN,
        Permission.SEND_ANNOUNCEMENTS,
    },
    UserRole.MODERATOR: {
        Permission.BAN_USERS,
        Permission.KICK_USERS,
        Permission.MUTE_USERS,
        Permission.WARN_USERS,
        Permission.DELETE_MESSAGES,
        Permission.PIN_MESSAGES,
        Permission.MANAGE_KNOWLEDGE,
        Permission.MANAGE_FILTERS,
        Permission.VIEW_LOGS,
    },
    UserRole.HELPER: {
        Permission.WARN_USERS,
        Permission.DELETE_MESSAGES,
        Permission.MANAGE_KNOWLEDGE,
    },
    UserRole.VIP: {
        Permission.PIN_MESSAGES,
    },
    UserRole.TRUSTED: set(),
    UserRole.MEMBER: set(),
    UserRole.MUTED: set(),
    UserRole.BLACKLISTED: set(),
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def can_moderate_target(actor_role: UserRole, target_role: UserRole) -> bool:
    hierarchy = {
        UserRole.OWNER: 100,
        UserRole.MANAGER: 80,
        UserRole.MODERATOR: 60,
        UserRole.HELPER: 40,
        UserRole.VIP: 30,
        UserRole.TRUSTED: 20,
        UserRole.MEMBER: 10,
        UserRole.MUTED: 0,
        UserRole.BLACKLISTED: 0,
    }
    return hierarchy.get(actor_role, 0) > hierarchy.get(target_role, 0)
