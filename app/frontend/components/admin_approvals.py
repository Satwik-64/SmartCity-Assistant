"""Streamlit views for managing pending authority approvals."""
from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from frontend.api_client import api_delete, api_get, api_patch


def _handle_response_error(response: Any, action: str) -> None:
    """Render a helpful error box when backend calls fail."""
    detail = ""
    try:
        detail = response.json().get("detail", "")  # type: ignore[call-arg]
    except Exception:
        detail = ""
    message = detail or f"Unable to {action}."
    st.error(f"❌ {message}")


def _render_authority_card(authority: Dict[str, Any]) -> None:
    """Render a single approval card with action buttons."""
    authority_id = authority.get("id")
    if authority_id is None:
        return

    with st.container():
        st.markdown(
            f"""
            <div class="approval-card">
                <div class="approval-card__header">
                    <h3>{authority.get('name', 'Unknown')}</h3>
                    <span class="approval-card__chip">{authority.get('position', 'No position')}</span>
                </div>
                <div class="approval-card__meta">
                    <div><strong>Feedback route:</strong> {authority.get('feedback_route') or 'Not assigned'}</div>
                    <div><strong>Phone:</strong> {authority.get('phone_number') or '---'}</div>
                    <div><strong>Email:</strong> {authority.get('email') or '---'}</div>
                    <div><strong>Created:</strong> {authority.get('created_at') or '---'}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(f"approve_authority_{authority_id}"):
            col_approve, col_reject = st.columns(2)
            approve_clicked = col_approve.form_submit_button("✅ Approve", use_container_width=True)
            reject_clicked = col_reject.form_submit_button("🗑️ Reject", use_container_width=True)

            if approve_clicked:
                response = api_patch(
                    f"/auth/admin/authorities/{authority_id}/approve",
                    json={"approve": True},
                )
                if response.status_code == 200:
                    st.success("🎉 Authority approved successfully.")
                    st.rerun()
                else:
                    _handle_response_error(response, "approve authority")

            if reject_clicked:
                response = api_delete(f"/auth/admin/authorities/{authority_id}")
                if response.status_code == 204:
                    st.warning("🚫 Authority registration rejected.")
                    st.rerun()
                else:
                    _handle_response_error(response, "reject authority")


def render_authority_approvals() -> None:
    """Render the admin approvals dashboard."""
    st.title("Authority approvals")
    st.caption("Review pending authority registrations and activate eligible accounts.")

    user = st.session_state.get("user_data") or {}
    if not bool(user.get("is_admin")):
        st.error("Admin privileges are required to view this page.")
        return

    st.markdown(
        """
        <style>
        .approval-card {
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 22px;
            backdrop-filter: blur(16px);
        }
        .approval-card__header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .approval-card__header h3 {
            margin: 0;
            color: #f8fafc;
        }
        .approval-card__chip {
            background: rgba(59, 130, 246, 0.25);
            border: 1px solid rgba(59, 130, 246, 0.45);
            color: #bfdbfe;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.85rem;
        }
        .approval-card__meta {
            display: grid;
            gap: 6px;
            color: #cbd5f5;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        response = api_get("/auth/admin/authorities/pending")
    except Exception as exc:  # pragma: no cover - defensive UI guard
        st.error(f"Unable to load pending authorities: {exc}")
        return

    if response.status_code in (401, 403):
        _handle_response_error(response, "load pending authorities")
        return

    if not response.ok:
        _handle_response_error(response, "load pending authorities")
        return

    pending: List[Dict[str, Any]] = response.json()
    if not pending:
        st.success("✅ No pending authority registrations. You're all caught up!")
        return

    st.info(
        "Review each request carefully. Approved accounts become active immediately and can access the dashboard."
    )

    for authority in pending:
        _render_authority_card(authority)
