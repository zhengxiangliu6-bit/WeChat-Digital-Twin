# coding: utf-8
"""Load crj persona files and build the system prompt.

Design: system prompt = distilled behavior rules (SKILL.md) only.
Raw quotes (voice.md) stay as human-readable research evidence.
Slang dictionary is injected only when user input matches entries.
"""

import json
import os

_SKILL_PATH = os.path.join("output", "friend", "SKILL.md")
_SLANG_PATH = os.path.join("data", "slang.json")


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _strip_yaml_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].lstrip("\n")
    return text


def _load_slang_dict(project_root: str) -> list[dict]:
    path = os.path.join(project_root, _SLANG_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def match_slang(project_root: str, user_text: str) -> str:
    """Return slang explanations for terms found in user_text.

    Only returns entries whose keyword appears in the input.
    Returns empty string if no matches.
    """
    entries = _load_slang_dict(project_root)
    if not entries:
        return ""

    matched = []
    for entry in entries:
        keyword = entry.get("term", "")
        if keyword and keyword in user_text:
            meaning = entry.get("meaning", "")
            if meaning:
                matched.append(f"- {keyword}：{meaning}")

    if not matched:
        return ""

    return "以下网络用语出现在对方消息中，供理解参考（不要强制使用）：\n" + "\n".join(matched)


def load_system_prompt(project_root: str) -> str:
    """Build system prompt from SKILL.md only."""
    skill = _read_file(os.path.join(project_root, _SKILL_PATH))

    if not skill:
        raise FileNotFoundError(
            f"SKILL.md not found at {os.path.join(project_root, _SKILL_PATH)}"
        )

    skill = _strip_yaml_frontmatter(skill)

    parts = [
        "你是 crj 的 AI 数字分身，基于他的微信群聊风格模拟。",
        "这不是 crj 本人。不要编造他的真实经历或当前想法。",
        "",
        "回复原则：",
        "- 像朋友聊天，不刻意表演，但保持 crj 的说话特点。",
        "- 回复长度由对话内容决定：简单回应可以一句话，讲故事或接梗时可以多条。",
        "- 不要每轮都搞笑，但在对方给了笑点时要敢接敢玩。",
        "- 不要主动搬出历史上说过的具体句子。",
        "- 认真的问题认真回答。",
        "- 多条消息用换行分隔。",
        "",
        skill,
    ]

    return "\n".join(parts)


def get_persona_name() -> str:
    return "crj"


def get_disclaimer() -> str:
    return "AI 数字分身，不是陈荣君本人。"
