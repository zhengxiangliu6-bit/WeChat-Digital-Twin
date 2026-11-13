"""Streamlit chat UI for crj AI digital twin."""

import logging
import os
import sys

# Project root is one level up from app/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Set up logging to file for diagnostics
logging.basicConfig(
    filename=os.path.join(PROJECT_ROOT, "chat_debug.log"),
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    encoding="utf-8",
)

import streamlit as st
from app.persona import load_system_prompt, get_persona_name, get_disclaimer, match_slang
from app.database import init_db, create_conversation, list_conversations, get_messages, add_message, delete_conversation
from app.llm import chat


# --- Init ---
init_db(PROJECT_ROOT)

# Load persona once
if "system_prompt" not in st.session_state:
    try:
        st.session_state.system_prompt = load_system_prompt(PROJECT_ROOT)
        st.session_state.persona_loaded = True
    except FileNotFoundError as e:
        st.session_state.system_prompt = ""
        st.session_state.persona_loaded = False
        st.session_state.persona_error = str(e)


# --- Page config ---
st.set_page_config(
    page_title=f"{get_persona_name()} AI",
    page_icon="💬",
    layout="centered",
)


# --- Sidebar: conversation list ---
with st.sidebar:
    st.title(f"{get_persona_name()} AI")
    st.caption(get_disclaimer())
    st.divider()

    if st.button("新建对话", use_container_width=True, type="primary"):
        new_id = create_conversation(PROJECT_ROOT)
        st.session_state.current_conv = new_id
        st.rerun()

    st.subheader("历史对话")
    convs = list_conversations(PROJECT_ROOT)
    for conv in convs:
        col1, col2 = st.columns([5, 1])
        with col1:
            is_current = st.session_state.get("current_conv") == conv["id"]
            label = f"{'▶ ' if is_current else ''}{conv['title']}"
            if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.current_conv = conv["id"]
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{conv['id']}"):
                delete_conversation(PROJECT_ROOT, conv["id"])
                if st.session_state.get("current_conv") == conv["id"]:
                    st.session_state.pop("current_conv", None)
                st.rerun()


# --- Main area ---
if not st.session_state.get("persona_loaded"):
    st.error(f"人物档案加载失败：{st.session_state.get('persona_error', '未知错误')}")
    st.stop()

# Ensure a conversation exists
if "current_conv" not in st.session_state:
    convs = list_conversations(PROJECT_ROOT)
    if convs:
        st.session_state.current_conv = convs[0]["id"]
    else:
        st.session_state.current_conv = create_conversation(PROJECT_ROOT)

conv_id = st.session_state.current_conv

# Load messages
messages = get_messages(PROJECT_ROOT, conv_id)

# Display messages
for msg in messages:
    role = msg["role"]
    with st.chat_message("assistant" if role == "assistant" else "user",
                         avatar="🤖" if role == "assistant" else "🧑"):
        # crj-style: split by newlines into separate visual "bubbles"
        if role == "assistant":
            lines = [l.strip() for l in msg["content"].split("\n") if l.strip()]
            for line in lines:
                st.markdown(line)
        else:
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("说点什么..."):
    # Show user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    add_message(PROJECT_ROOT, conv_id, "user", prompt)

    # Build API messages
    api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
    api_msgs.append({"role": "user", "content": prompt})

    # Inject slang context if user input matches known terms
    slang_note = match_slang(PROJECT_ROOT, prompt)
    effective_prompt = st.session_state.system_prompt
    if slang_note:
        effective_prompt = effective_prompt + "\n\n" + slang_note

    # Call LLM
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("crj 正在想..."):
            try:
                result = chat(effective_prompt, api_msgs)
                # Display crj-style multi-line
                lines = [l.strip() for l in result.content.split("\n") if l.strip()]
                for line in lines:
                    st.markdown(line)
                add_message(PROJECT_ROOT, conv_id, "assistant", result.content)
                # Show truncation warning if response was cut off
                if result.finish_reason == "length":
                    detail = f"completion={result.completion_tokens}"
                    if result.reasoning_tokens > 0:
                        detail += f", reasoning={result.reasoning_tokens}"
                    st.caption(f"⚠️ 回复被截断 ({detail})")
            except (ValueError, ConnectionError) as e:
                st.error(str(e))
