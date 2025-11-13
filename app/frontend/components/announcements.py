"""Announcements UI for authorities and citizens.

Provides a simple list view for all users and a creation form for authorities.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from app.frontend.api_client import api_get, api_post, api_delete


def _list_announcements() -> list[dict[str, Any]]:
    try:
        resp = api_get("/announcements/")
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return []


def render_announcements() -> None:
    user_type = st.session_state.get("user_type", "user") or "user"
    user_data = st.session_state.get("user_data") or {}
    user_id = user_data.get("id")
    feedback_route = (user_data.get("feedback_route") or "").strip().lower()
    is_mayor_route = feedback_route == "mayor's office"

    st.markdown("### Announcements")

    st.session_state.setdefault("_announcements_needs_refresh", False)
    refresh_needed = st.session_state.pop("_announcements_needs_refresh", False)

    if user_type == "authority":
        with st.expander("Create new announcement", expanded=False):
            with st.form("create_announcement"):
                title = st.text_input("Title")
                audience = st.text_input("Audience (optional)")
                content = st.text_area("Content")
                submitted = st.form_submit_button("Publish")
                if submitted:
                    if not title.strip() or not content.strip():
                        st.error("Title and content are required")
                    else:
                        payload = {"title": title.strip(), "content": content.strip(), "audience": audience or None}
                        resp = api_post("/announcements/", json=payload)
                        if resp.status_code == 201:
                            st.success("Announcement published")
                            st.session_state["_announcements_needs_refresh"] = True
                        else:
                            st.error(resp.json().get("detail", "Failed to publish"))

    rows = _list_announcements()
    if refresh_needed:
        rows = _list_announcements()
    if not rows:
        st.info("No announcements published yet.")
        return

    for a in rows:
        header = f"**{a.get('title')}**  \n_by {a.get('author_name') or 'Unknown'} • {a.get('created_at')}_"
        st.markdown(header)
        st.write(a.get("content"))
        if user_type == "authority":
            author_id = a.get("author_id")
            can_delete = (author_id == user_id) or is_mayor_route
            if can_delete and st.button(f"Delete {a.get('id')}", key=f"del_{a.get('id')}"):
                resp = api_delete(f"/announcements/{a.get('id')}")
                if resp.status_code in (200, 204):
                    st.success("Deleted")
                    st.session_state["_announcements_needs_refresh"] = True
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete announcement")
        st.markdown("---")


if __name__ == "__main__":
    render_announcements()
