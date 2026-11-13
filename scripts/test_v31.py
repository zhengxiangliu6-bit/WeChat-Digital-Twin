# coding: utf-8
"""Verify v3.1 changes: prompt structure, slang matching, no regressions."""
import io, sys, os, json, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

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

# === 1. System prompt ===
print("=== System prompt ===")
from app.persona import load_system_prompt, match_slang
p = load_system_prompt('.')
print(f"  Length: {len(p)} chars")

check("No raw crj: quotes", "crj:" not in p)
check("No v我102", "v我102" not in p)
check("No v我900", "v我900" not in p)
check("No 我付出真心", "我付出真心" not in p)
check("No 吃点脑残片", "吃点脑残片" not in p)
check("No voice.md content", "原话样本参考" not in p)
check("No dialogue-patterns content", "对话策略参考" not in p and "对话行为模式库" not in p)

# Check distinctiveness markers are present
check("Has 7哈 marker", "7个哈" in p or "七个哈" in p)
check("Has 我说 marker", "我说" in p)
check("Has 第三人称 marker", "第三人称" in p)
check("Has 反问 pattern", "反问" in p)
check("Has 冷幽默 pattern", "冷幽默" in p)
check("Has OK marker", "OK" in p)

# Check brevity is NOT forced
check("No forced one-line rule", "一句话就够了" not in p)
check("No forced 一两句话", "一两句话" not in p,
      "Found forced brevity instruction")
check("Length flexibility", "回复长度由对话" in p or "由对话内容决定" in p,
      "Missing flexible length instruction")

print()

# === 2. Slang dictionary ===
print("=== Slang dictionary ===")
slang_path = os.path.join(proj, "data", "slang.json")
check("slang.json exists", os.path.exists(slang_path))

with open(slang_path, "r", encoding="utf-8") as f:
    slang = json.load(f)
check("Has entries", len(slang) > 0, f"Got {len(slang)}")
check("All entries have term+meaning",
      all(e.get("term") and e.get("meaning") for e in slang))
check("All entries have verified flag",
      all("verified" in e for e in slang))
print(f"  Entries: {len(slang)}")

# Test match_slang function
result = match_slang('.', "今天疯狂星期四v我50")
check("Matches v我", "v我" in result)
check("Matches 疯狂星期四", "疯狂星期四" in result)
check("Contains '不要强制使用'", "不要强制使用" in result)

result_empty = match_slang('.', "今天天气真好")
check("No match for unrelated input", result_empty == "")

print()

# === 3. LLM params ===
print("=== LLM params ===")
import app.llm as llm_mod
source = inspect.getsource(llm_mod.chat)
check("temperature=0.75", "temperature=0.75" in source)
check("max_tokens=512", "max_tokens=512" in source)

print()

# === 4. Database not broken ===
print("=== Database ===")
test_db = 'test_v31.db'
if os.path.exists(test_db):
    os.remove(test_db)
import app.database as db_mod
original_db = db_mod._DB_NAME
db_mod._DB_NAME = test_db
from app.database import init_db, create_conversation, add_message, get_messages
init_db('.')
cid = create_conversation('.')
add_message('.', cid, 'user', 'hello')
add_message('.', cid, 'assistant', 'test reply')
msgs = get_messages('.', cid)
check("DB read/write works", len(msgs) == 2)
db_mod._DB_NAME = original_db
os.remove(test_db)

print()
print(f"=== RESULTS: {passed} passed, {failed} failed ===")
if failed:
    sys.exit(1)
