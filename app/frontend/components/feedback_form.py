"""Role-aware feedback experience for citizens and authorities."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, cast

import html

import pandas as pd
import streamlit as st

from app.frontend.api_client import api_get, api_patch, api_post

STATUS_ORDER = ["reported", "in_process", "solved"]
STATUS_LABELS = {
    "reported": "Reported",
    "in_process": "In Process",
    "solved": "Solved",
}
AUTHORITY_OPTIONS: List[str] = [
    "Mayor's Office",
    "City Council",
    "Public Works Department",
    "Transportation Authority",
    "Environmental Services",
    "Health & Safety Department",
    "Housing & Urban Development",
]


def _label_for_status(value: Optional[str]) -> str:
    if not value:
        return "Unknown"
    return STATUS_LABELS.get(value, value.replace("_", " ").title())


def render_feedback_header(user_type: str) -> None:
    user = st.session_state.get("user_data", {}) or {}
    display_name = html.escape(user.get("name") or "Citizen")
    role_label = "Authority" if user_type == "authority" else "Citizen"

    st.markdown(
        f"""
        <div class="hero-banner" style="margin-bottom:1.5rem;">
            <div>
                <div class="chip">Feedback workflows</div>
                <h1 class="hero-banner__title">Feedback centre</h1>
                <p class="hero-banner__subtitle">
                    Submit observations and track how city teams resolve them through a single, citywide pipeline.
                </p>
            </div>
            <div class="metric-stack" style="min-width:240px;">
                <div class="metric-block">
                    <span class="metric-block__label">Signed in</span>
                    <span class="metric-block__value">{display_name}</span>
                </div>
                <div class="metric-block">
                    <span class="metric-block__label">Role</span>
                    <span class="metric-block__value">{role_label}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feedback_section() -> None:
    user_type = st.session_state.get("user_type", "user") or "user"
    render_feedback_header(user_type)

    if user_type == "authority":
        render_authority_console()
    else:
        render_citizen_console()


def render_citizen_console() -> None:
    with st.container():
        st.markdown(
            "<div class='glass-panel'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='margin-top:0;'>Submit new feedback</h3>",
            unsafe_allow_html=True,
        )

        with st.form("citizen_feedback_form", clear_on_submit=True):
            col_primary = st.columns(2)
            category = col_primary[0].selectbox(
                "Category",
                [
                    "Environmental Issues",
                    "Public Transportation",
                    "Waste Management",
                    "Water Quality",
                    "Energy Efficiency",
                    "Urban Planning",
                    "Public Health",
                    "Education",
                    "Economic Development",
                    "Other",
                ],
            )
            priority = col_primary[1].select_slider(
                "Priority",
                options=["Low", "Medium", "High", "Critical"],
                value="Low",
            )
            authority_type = st.selectbox("Route to", AUTHORITY_OPTIONS)
            location = st.text_input("Location", placeholder="Downtown, Ward 12, etc.")
            message = st.text_area(
                "Describe the issue",
                placeholder="Share relevant context, current impact, and any supporting details...",
            )
            submitted = st.form_submit_button("Submit feedback", use_container_width=True)

            if submitted:
                if not message.strip():
                    st.warning("Please provide a description before submitting.")
                else:
                    payload = {
                        "category": category,
                        "message": message.strip(),
                        "priority": priority,
                        "authority_type": authority_type,
                        "location": location.strip() or None,
                    }
                    response = api_post("/feedback/submit", json=payload)
                    if response.status_code == 201:
                        st.success("Thank you! Your feedback has been recorded.")
                    else:
                        st.error(_extract_error(response))

        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown(
            "<div class='glass-panel' style='margin-top:1.5rem;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='margin-top:0;'>Your submissions</h3>",
            unsafe_allow_html=True,
        )
        entries = _load_my_feedback()
        if not entries:
            st.info("No feedback submitted yet. Use the form above to share your first report.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        st.dataframe(_format_feedback_table(entries), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_authority_console() -> None:
    with st.container():
        st.markdown(
            "<div class='glass-panel'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='margin-top:0;'>Manage citizen submissions</h3>",
            unsafe_allow_html=True,
        )
        filter_col, hint_col = st.columns([1, 2])
        statuses = ["All"] + [STATUS_LABELS[key] for key in STATUS_ORDER]
        selection = cast(str, filter_col.selectbox("Filter by status", statuses))
        status_query: Optional[str] = None
        if selection and selection != "All":
            inverse = {value: key for key, value in STATUS_LABELS.items()}
            status_query = inverse.get(selection)
        route_label = (st.session_state.get("user_data", {}) or {}).get("feedback_route")
        if route_label:
            hint_col.caption(
                f"Review incoming reports routed to **{html.escape(route_label)}** and update their status.",
                unsafe_allow_html=True,
            )
        else:
            hint_col.caption(
                "Review incoming reports, update notes, and move cases through the resolution workflow.",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    entries = _load_manage_feedback(status_query)
    if not entries:
        st.info("No feedback matches the selected filter.")
        return

    status_map = {v: k for k, v in STATUS_LABELS.items()}

    for record in entries:
        status_display = _label_for_status(record.get("status"))
        with st.expander(
            f"{status_display.upper()} • {record.get('category', 'General')} • {record.get('citizen_name') or 'Citizen'}",
            expanded=False,
        ):
            st.write(record["message"])
            meta_cols = st.columns(3)
            meta_cols[0].write(f"📍 **Location:** {record.get('location') or 'Not provided'}")
            meta_cols[1].write(f"📞 **Contact:** {record.get('citizen_contact') or 'Hidden'}")
            created = _format_datetime(record.get("created_at"))
            meta_cols[2].write(f"🗓️ **Submitted:** {created}")

            current_status = record.get("status") or "reported"
            current_notes = record.get("authority_notes", "")

            with st.form(f"update_{record['id']}"):
                col_upd = st.columns([1, 2])
                new_status_label = cast(
                    str,
                    col_upd[0].selectbox(
                        "Status",
                        [STATUS_LABELS[key] for key in STATUS_ORDER],
                        index=STATUS_ORDER.index(current_status) if current_status in STATUS_ORDER else 0,
                    ),
                )
                notes = col_upd[1].text_area("Authority notes", value=current_notes or "", height=80)
                submitted = st.form_submit_button("Update status", use_container_width=True)

                if submitted:
                    status_value = status_map.get(new_status_label, current_status)
                    payload = {"status": status_value, "authority_notes": notes or None}
                    response = api_patch(f"/feedback/{record['id']}", json=payload)
                    if response.status_code == 200:
                        st.success("Feedback updated.")
                        st.experimental_rerun()
                    else:
                        st.error(_extract_error(response))


def _load_my_feedback() -> List[Dict[str, Optional[str]]]:
    try:
        response = api_get("/feedback/my")
        if response.ok:
            return response.json()
    except Exception:
        return []
    return []


def _load_manage_feedback(status_filter: Optional[str]) -> List[Dict[str, Optional[str]]]:
    params = {"status_filter": status_filter} if status_filter else {}
    try:
        response = api_get("/feedback/manage", params=params)
        if response.ok:
            return response.json()
    except Exception:
        return []
    return []


def _format_feedback_table(entries: List[Dict[str, Optional[str]]]) -> pd.DataFrame:
    rows = []
    for entry in entries:
        status_label = _label_for_status(entry.get("status"))
        rows.append(
            {
                "Category": entry.get("category"),
                "Priority": entry.get("priority") or "--",
                "Status": status_label,
                "Authority": entry.get("authority_name") or entry.get("authority_type") or "Triage",
                "Last updated": _format_datetime(entry.get("updated_at")),
                "Submitted": _format_datetime(entry.get("created_at")),
            }
        )

    df = pd.DataFrame(rows)
    return df


def _format_datetime(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            parsed = value
        return parsed.strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(value)


def _extract_error(response) -> str:
    try:
        detail = response.json().get("detail")
        if isinstance(detail, str):
            return detail
    except Exception:
        pass
    return "Request failed. Please try again."


def render_feedback_form() -> None:
    render_feedback_section()


if __name__ == "__main__":
    render_feedback_form()