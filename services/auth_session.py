import json

import flet as ft


USER_PREFERENCE_KEY = "hows_business.user"


async def persist_user(page: ft.Page, user: dict) -> None:
    """Keep the non-sensitive user profile available after a browser reconnect."""
    page.session.store.set("user", user)
    try:
        await page.shared_preferences.set(USER_PREFERENCE_KEY, json.dumps(user))
    except Exception:
        # The in-memory login still works if browser storage is unavailable.
        pass


async def restore_user(page: ft.Page) -> dict | None:
    user = page.session.store.get("user")
    if user:
        return user

    try:
        stored = await page.shared_preferences.get(USER_PREFERENCE_KEY)
    except Exception:
        return None
    if not isinstance(stored, str):
        return None

    try:
        user = json.loads(stored)
    except (TypeError, ValueError):
        await page.shared_preferences.remove(USER_PREFERENCE_KEY)
        return None

    if not isinstance(user, dict) or not user.get("user_no") or not user.get("email"):
        await page.shared_preferences.remove(USER_PREFERENCE_KEY)
        return None

    page.session.store.set("user", user)
    return user


async def clear_user(page: ft.Page) -> None:
    if page.session.store.contains_key("user"):
        page.session.store.remove("user")
    try:
        await page.shared_preferences.remove(USER_PREFERENCE_KEY)
    except Exception:
        pass
