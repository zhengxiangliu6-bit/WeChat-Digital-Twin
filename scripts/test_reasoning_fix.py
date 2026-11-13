# coding: utf-8
"""End-to-end test: verify reasoning_effort=low fixes the truncation issue."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

from dotenv import load_dotenv
load_dotenv(os.path.join(proj, ".env"))

# Ensure reasoning_effort=low is set (default from code)
# Don't override if user already set it in .env

from app.persona import load_system_prompt
from app.llm import chat, _get_reasoning_effort

system_prompt = load_system_prompt(".")
re = _get_reasoning_effort()
print(f"reasoning_effort: {re}")
print(f"system prompt: {len(system_prompt)} chars")
print()

# The exact message that caused the "我说" truncation
test_msg = "笑死 我跟你说 我同事车被划了，让我帮他看监控，还让我不要在上班的时候看"
api_msgs = [{"role": "user", "content": test_msg}]

print(f"User: {test_msg}")
print()

result = chat(system_prompt, api_msgs)

print(f"Content ({len(result.content)} chars): {result.content}")
print(f"finish_reason: {result.finish_reason}")
print(f"prompt_tokens: {result.prompt_tokens}")
print(f"completion_tokens: {result.completion_tokens}")
print(f"reasoning_tokens: {result.reasoning_tokens}")
print()

# Verify
passed = 0
failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} -- {detail}")
        failed += 1

check("finish_reason is stop", result.finish_reason == "stop",
      f"got {result.finish_reason}")
check("content is not just '我说'", result.content != "我说",
      f"got {repr(result.content)}")
check("content length > 5 chars", len(result.content) > 5,
      f"got {len(result.content)} chars")
check("reasoning_tokens = 0 with low effort", result.reasoning_tokens == 0,
      f"got {result.reasoning_tokens}")
check("no truncation", result.finish_reason != "length")

print(f"\n=== {passed} passed, {failed} failed ===")
if failed:
    sys.exit(1)
