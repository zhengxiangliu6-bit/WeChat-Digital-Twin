# coding: utf-8
"""Inspect the actual system prompt sent to the model."""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(proj)
sys.path.insert(0, proj)

from app.persona import load_system_prompt
p = load_system_prompt('.')

print(f'Total system prompt: {len(p)} chars')
print()

# Find section headers
print('=== SECTIONS ===')
for line in p.split('\n'):
    stripped = line.strip()
    if stripped.startswith('=====') or stripped.startswith('## ') or stripped.startswith('# '):
        print(f'  {stripped}')
print()

# Count raw quote lines (lines starting with "crj:")
crj_lines = [l for l in p.split('\n') if l.strip().startswith('crj:')]
print(f'Lines starting with "crj:" (raw quotes): {len(crj_lines)}')
for l in crj_lines[:10]:
    print(f'  {l.strip()[:70]}')
if len(crj_lines) > 10:
    print(f'  ... and {len(crj_lines) - 10} more')
print()

# Estimate quote vs rule content
triple_bt = '`' * 3
in_block = False
block_chars = 0
for line in p.split('\n'):
    if line.strip().startswith(triple_bt):
        in_block = not in_block
        continue
    if in_block:
        block_chars += len(line)

print(f'Chars inside code blocks (raw quotes): {block_chars} ({block_chars*100//len(p)}%)')
print(f'Chars outside code blocks (rules/instructions): {len(p)-block_chars} ({(len(p)-block_chars)*100//len(p)}%)')
print()

# Check for specific problematic content
problems = ['v我102', 'v我50', 'v我900', '立省百分百', '不活了', '吃点脑残片',
            '当场把头摘下来', '我付出真心']
print('=== Specific raw quotes found in prompt ===')
for phrase in problems:
    if phrase in p:
        # Find context
        idx = p.index(phrase)
        context = p[max(0,idx-30):idx+len(phrase)+30].replace('\n', ' | ')
        print(f'  FOUND: "{phrase}" -> ...{context}...')
    else:
        print(f'  not found: "{phrase}"')
