# coding: utf-8
"""Diagnose GLM-5.3 reasoning model behavior on Alibaba Cloud Bailian.

Checks:
1. Whether max_tokens includes reasoning tokens
2. What reasoning_effort does
3. Response structure (reasoning_content vs content)
4. Token usage breakdown
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

from dotenv import load_dotenv
load_dotenv(os.path.join(proj, ".env"))

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=60.0,
)
model = os.environ.get("OPENAI_MODEL", "glm-5.3")

TEST_MSG = [
    {"role": "system", "content": "你是一个朋友，用简短的中文回复。"},
    {"role": "user", "content": "今天天气怎么样"},
]

def run_test(label, **extra_kwargs):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Params: model={model}, {extra_kwargs}")
    print(f"{'='*60}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=TEST_MSG,
            **extra_kwargs,
        )
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return

    choice = response.choices[0] if response.choices else None
    if not choice:
        print("ERROR: No choices in response")
        return

    # Content
    content = choice.message.content or ""
    print(f"\ncontent: {repr(content[:200])}")
    print(f"content length: {len(content)} chars")
    print(f"finish_reason: {choice.finish_reason}")

    # Check for reasoning_content (non-standard field)
    msg = choice.message
    reasoning = getattr(msg, 'reasoning_content', None)
    if reasoning is None:
        # Try dict access for dynamic attributes
        try:
            msg_dict = msg.model_dump() if hasattr(msg, 'model_dump') else {}
            reasoning = msg_dict.get('reasoning_content')
        except:
            pass
    if reasoning:
        print(f"\nreasoning_content: {repr(reasoning[:200])}...")
        print(f"reasoning_content length: {len(reasoning)} chars")
    else:
        print(f"\nreasoning_content: NOT PRESENT")

    # Token usage
    if response.usage:
        u = response.usage
        print(f"\nToken usage:")
        print(f"  prompt_tokens: {u.prompt_tokens}")
        print(f"  completion_tokens: {u.completion_tokens}")
        print(f"  total_tokens: {u.total_tokens}")
        # Check for reasoning_tokens (some providers include this)
        try:
            u_dict = u.model_dump() if hasattr(u, 'model_dump') else {}
            for k, v in u_dict.items():
                if k not in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
                    print(f"  {k}: {v}")
        except:
            pass
    else:
        print("\nToken usage: NOT AVAILABLE")

    # Raw response dump for inspection
    try:
        raw = response.model_dump()
        # Remove message content for privacy, keep structure
        if 'choices' in raw and raw['choices']:
            c = raw['choices'][0]
            if 'message' in c:
                if 'content' in c['message']:
                    c['message']['content'] = f"[{len(content)} chars]"
                if 'reasoning_content' in c['message']:
                    rc = c['message']['reasoning_content']
                    c['message']['reasoning_content'] = f"[{len(rc) if rc else 0} chars]"
        print(f"\nFull response structure:")
        print(json.dumps(raw, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"\nCould not dump response: {e}")


# Test 1: Low max_tokens (reproduce the truncation)
run_test("max_tokens=512, no reasoning_effort",
         max_tokens=512, temperature=0.75)

# Test 2: Low max_tokens with reasoning_effort=low
run_test("max_tokens=512, reasoning_effort=low",
         max_tokens=512, temperature=0.75,
         extra_body={"reasoning_effort": "low"})

# Test 3: Higher max_tokens
run_test("max_tokens=2048, reasoning_effort=low",
         max_tokens=2048, temperature=0.75,
         extra_body={"reasoning_effort": "low"})

print("\n" + "="*60)
print("DONE. Review the output above to determine:")
print("1. Whether completion_tokens includes reasoning tokens")
print("2. Whether reasoning_effort=low reduces reasoning token usage")
print("3. Whether finish_reason=length occurs with low max_tokens")
print("="*60)
