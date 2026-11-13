# coding: utf-8
"""Test llm.py changes: ChatResult, logging, configurable max_tokens."""
import io, sys, os, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

from dotenv import load_dotenv
load_dotenv(os.path.join(proj, ".env"))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} -- {detail}")
        failed += 1

# === 1. ChatResult structure ===
print("=== ChatResult ===")
from app.llm import ChatResult
r = ChatResult(content="test", finish_reason="stop", prompt_tokens=10, completion_tokens=5)
check("ChatResult has content", r.content == "test")
check("ChatResult has finish_reason", r.finish_reason == "stop")
check("ChatResult has prompt_tokens", r.prompt_tokens == 10)
check("ChatResult has completion_tokens", r.completion_tokens == 5)

# === 2. chat() return type ===
print("\n=== chat() signature ===")
from app.llm import chat
sig = inspect.signature(chat)
check("chat() returns ChatResult in annotations or docstring",
      "ChatResult" in str(sig.return_annotation) or "ChatResult" in (chat.__doc__ or ""),
      f"return annotation: {sig.return_annotation}")

# === 3. max_tokens configurable ===
print("\n=== MAX_TOKENS config ===")
from app.llm import _get_max_tokens
# Test with env var
os.environ["MAX_TOKENS"] = "2048"
check("MAX_TOKENS from env", _get_max_tokens() == 2048)
os.environ.pop("MAX_TOKENS", None)
check("MAX_TOKENS default is 1024", _get_max_tokens() == 1024)

# === 4. main.py uses result.content ===
print("\n=== main.py integration ===")
main_src = open(os.path.join(proj, "app", "main.py"), "r", encoding="utf-8").read()
check("Uses result.content", "result.content" in main_src)
check("Checks finish_reason=length", 'result.finish_reason == "length"' in main_src)
check("Shows truncation warning", "截断" in main_src or "truncat" in main_src.lower())
check("Has logging setup", "logging.basicConfig" in main_src)
check("Log file = chat_debug.log", "chat_debug.log" in main_src)

# === 5. .gitignore includes log ===
print("\n=== .gitignore ===")
gitignore = open(os.path.join(proj, ".gitignore"), "r", encoding="utf-8").read()
check("chat_debug.log in .gitignore", "chat_debug.log" in gitignore)

# === 6. Database still works ===
print("\n=== Database ===")
import app.database as db_mod
test_db = "test_llmfix.db"
if os.path.exists(test_db):
    os.remove(test_db)
original_db = db_mod._DB_NAME
db_mod._DB_NAME = test_db
from app.database import init_db, create_conversation, add_message, get_messages
init_db(".")
cid = create_conversation(".")
add_message(".", cid, "user", "hello")
add_message(".", cid, "assistant", "line1\nline2\nline3")
msgs = get_messages(".", cid)
check("DB stores multiline content", "\n" in msgs[1]["content"])
check("DB content complete", msgs[1]["content"] == "line1\nline2\nline3")
db_mod._DB_NAME = original_db
os.remove(test_db)

# === 7. Persona prompt unchanged ===
print("\n=== Persona prompt ===")
from app.persona import load_system_prompt
p = load_system_prompt(".")
check("No raw crj: quotes", "crj:" not in p)
check("No voice.md injection", "原话样本参考" not in p)

print(f"\n=== RESULTS: {passed} passed, {failed} failed ===")
if failed:
    sys.exit(1)
