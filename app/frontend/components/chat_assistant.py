# Streamlit chat assistant component with persistent history support.
from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from app.frontend.api_client import api_delete, api_get, api_post


def _current_user_id() -> Optional[int]:
    user_data = st.session_state.get("user_data")
    if isinstance(user_data, dict):
        return user_data.get("id")
    return None


def _load_persisted_history(user_id: int) -> List[Dict[str, Any]]:
    try:
        response = api_get("/chat/history")
        if response.status_code == 200:
            payload = response.json()
            history = payload.get("history", [])
            if isinstance(history, list):
                return history
    except Exception:
        pass
    return []


def _ensure_chat_history_loaded() -> None:
    st.session_state.setdefault("chat_history", [])
    user_id = _current_user_id()

    if user_id is not None and not st.session_state.get("chat_history_loaded"):
        st.session_state.chat_history = _load_persisted_history(user_id)
        st.session_state.chat_history_loaded = True
    elif user_id is None and "chat_history_loaded" not in st.session_state:
        st.session_state.chat_history_loaded = True


def _record_interaction(message: str, response: str, history: Optional[List[Dict[str, Any]]] = None) -> None:
    if history is not None:
        st.session_state.chat_history = history
        return

    timestamp = datetime.utcnow().isoformat()
    st.session_state.chat_history.extend(
        [
            {"sender": "user", "message": message, "timestamp": timestamp},
            {"sender": "assistant", "message": response, "timestamp": timestamp},
        ]
    )


def _export_history_text() -> str:
    if not st.session_state.get("chat_history"):
        return "No saved history."

    lines = ["Smart Assistant Conversation Log", ""]
    for item in st.session_state.chat_history:
        timestamp = item.get("timestamp", "--")
        message = item.get("message", "")
        response = item.get("response", "")
        lines.append(f"[{timestamp}] You: {message}")
        lines.append(f"[{timestamp}] Assistant: {response}")
        lines.append("")
    return "\n".join(lines)


def show_chat_assistant() -> None:
    """Render the chat assistant interface with persistent history."""

    st.markdown(
        """
        <style>
        .chat-bubble {
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.7rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(15, 23, 42, 0.62);
            box-shadow: 0 18px 44px rgba(8, 47, 73, 0.24);
            color: #e2e8f0;
            backdrop-filter: blur(16px);
        }
        .chat-bubble strong {
            display: block;
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #cbd5f5;
            margin-bottom: 0.35rem;
        }
        .chat-bubble--user {
            background: linear-gradient(135deg, rgba(56,189,248,0.26), rgba(14,165,233,0.16));
            border-color: rgba(56, 189, 248, 0.4);
        }
        .chat-bubble--assistant {
            background: linear-gradient(135deg, rgba(34,197,94,0.3), rgba(22,163,74,0.16));
            border-color: rgba(34, 197, 94, 0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("💬 Smart City Chat Assistant")
    st.caption(
        "Ask about sustainability policies, governance best practices, or city metrics — your conversation is now saved when logged in."
    )

    _ensure_chat_history_loaded()
    user_id = _current_user_id()

    if st.session_state.get("_pending_clear_chat_input"):
        st.session_state["chat_input"] = ""
        st.session_state["_pending_clear_chat_input"] = False

    user_message = st.text_input(
        "Your question",
        placeholder="e.g., How can we cut transport emissions by 30%?",
        key="chat_input",
    )

    send_clicked = st.button("Send 🚀", type="primary")

    if send_clicked and user_message.strip():
        payload: Dict[str, Any] = {"message": user_message}
        with st.spinner("Thinking..."):
            try:
                response = api_post("/chat/ask", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    history = data.get("history") if isinstance(data, dict) else None
                    assistant_reply = data.get("response", "") if isinstance(data, dict) else ""
                    parsed_history = history if isinstance(history, list) else None
                    _record_interaction(user_message, assistant_reply, parsed_history)
                    st.session_state["_pending_clear_chat_input"] = True
                    st.experimental_rerun()
                else:
                    st.error("The assistant could not process your request. Please try again.")
            except Exception as exc:  # pragma: no cover - defensive
                st.error(f"Unexpected error: {exc}")

    history = st.session_state.get("chat_history", [])

    st.divider()

    if not history:
        st.subheader("Latest response")
        st.info("No saved conversations yet. Start chatting to build your history.")
        return

    latest_exchange = history[-2:] if len(history) >= 2 else history
    latest_timestamp = latest_exchange[-1].get("timestamp", "")

    st.subheader("Latest response")
    st.caption(f"Last updated: {latest_timestamp or 'recently'}")

    for entry in latest_exchange:
        sender = entry.get("sender")
        message_text = entry.get("message") or entry.get("response") or ""
        timestamp = entry.get("timestamp", "")
        if sender == "user":
            bubble_class = "chat-bubble chat-bubble--user"
            label = "🙋 You"
        else:
            bubble_class = "chat-bubble chat-bubble--assistant"
            label = "🤖 Assistant"

        st.markdown(
            f"<div class='{bubble_class}'><strong>{label} • {timestamp}</strong><div>{html.escape(message_text)}</div></div>",
            unsafe_allow_html=True,
        )

    with st.expander("Conversation history", expanded=False):
        for entry in history:
            sender = entry.get("sender")
            message_text = entry.get("message") or entry.get("response") or ""
            timestamp = entry.get("timestamp", "")
            if sender == "user":
                bubble_class = "chat-bubble chat-bubble--user"
                label = "🙋 You"
            else:
                bubble_class = "chat-bubble chat-bubble--assistant"
                label = "🤖 Assistant"

            st.markdown(
                f"<div class='{bubble_class}'><strong>{label} • {timestamp}</strong><div>{html.escape(message_text)}</div></div>",
                unsafe_allow_html=True,
            )

        export_payload = json.dumps(history, ensure_ascii=False, indent=2)
        st.download_button(
            "Download history",
            export_payload,
            file_name="smart_assistant_history.json",
            mime="application/json",
            use_container_width=True,
        )

        if st.button("Delete history 🗑️", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state["_pending_clear_chat_input"] = True
            if user_id is not None:
                try:
                    response = api_delete("/chat/history")
                    if response.status_code not in (200, 204):
                        pass
                except Exception:
                    pass
            st.experimental_rerun()
