# coding: utf-8
"""Diagnose GLM-5.3 with the ACTUAL crj system prompt."""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

from dotenv import load_dotenv
load_dotenv(os.path.join(proj, ".env"))

from openai import OpenAI
from app.persona import load_system_prompt

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=60.0,
)
model = os.environ.get("OPENAI_MODEL", "glm-5.3")
system_prompt = load_system_prompt(".")

# The problematic user message
user_msg = "笑死 我跟你说 我同事车被划了，让我帮他看监控，还让我不要在上班的时候看"

TEST_MSGS = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_msg},
]

print(f"System prompt length: {len(system_prompt)} chars")
print(f"User message: {user_msg}")
print()

def run_test(label, **extra_kwargs):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"{'='*60}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=TEST_MSGS,
            **extra_kwargs,
        )
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return

    choice = response.choices[0]
    content = choice.message.content or ""
    print(f"finish_reason: {choice.finish_reason}")
    print(f"content ({len(content)} chars): {repr(content[:300])}")

    # Reasoning content
    msg_dict = choice.message.model_dump() if hasattr(choice.message, 'model_dump') else {}
    rc = msg_dict.get('reasoning_content', '')
    if rc:
        print(f"reasoning_content ({len(rc)} chars): {repr(rc[:200])}...")
    else:
        print(f"reasoning_content: EMPTY")

    # Token usage
    if response.usage:
        u = response.usage
        u_dict = u.model_dump() if hasattr(u, 'model_dump') else {}
        print(f"prompt_tokens: {u.prompt_tokens}")
        print(f"completion_tokens: {u.completion_tokens}")
        details = u_dict.get('completion_tokens_details', {})
        if details:
            rt = details.get('reasoning_tokens', 'N/A')
            print(f"reasoning_tokens: {rt}")
        print(f"total_tokens: {u.total_tokens}")


# Test 1: max_tokens=512 (the original failing config)
run_test("max_tokens=512 (original)",
         max_tokens=512, temperature=0.75)

# Test 2: max_tokens=512 + reasoning_effort=low
run_test("max_tokens=512, reasoning_effort=low",
         max_tokens=512, temperature=0.75,
         extra_body={"reasoning_effort": "low"})

# Test 3: max_tokens=1024 (current default)
run_test("max_tokens=1024 (current)",
         max_tokens=1024, temperature=0.75)

# Test 4: max_tokens=1024 + reasoning_effort=low
run_test("max_tokens=1024, reasoning_effort=low",
         max_tokens=1024, temperature=0.75,
         extra_body={"reasoning_effort": "low"})

print("\n" + "="*60)
print("Compare reasoning_tokens across tests.")
print("If reasoning_tokens > 0 with full prompt, that's the cause.")
print("="*60)
