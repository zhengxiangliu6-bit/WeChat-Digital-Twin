"""Extract language stats for target speaker from chat.md"""
import re
import sys
import io
from collections import Counter
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TARGET = '心理咨🐻师lzx'
CHAT_FILE = 'data/raw/chat.md'

def parse_messages(filepath, speaker_filter=None):
    msgs = []
    current_speaker = None
    current_ts = None
    current_lines = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = re.match(r'^\*\*(.+?)\*\* · (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$', line)
            if m:
                if current_speaker and current_lines:
                    text = '\n'.join(current_lines).strip()
                    if text and (speaker_filter is None or current_speaker == speaker_filter):
                        msgs.append((current_speaker, current_ts, text))
                current_speaker = m.group(1)
                current_ts = m.group(2)
                current_lines = []
            elif line.strip() == '' or line.startswith('---'):
                continue
            elif current_speaker:
                current_lines.append(line)

    if current_speaker and current_lines:
        text = '\n'.join(current_lines).strip()
        if text and (speaker_filter is None or current_speaker == speaker_filter):
            msgs.append((current_speaker, current_ts, text))
    return msgs

def main():
    print(f"Parsing chat for: {TARGET}")
    msgs = parse_messages(CHAT_FILE, TARGET)
    texts = [m[2] for m in msgs]

    print(f"Total messages: {len(msgs)}")
    print(f"Date range: {msgs[0][1][:10]} to {msgs[-1][1][:10]}")

    # Length
    lengths = [len(t) for t in texts]
    print(f"\n=== Length ===")
    print(f"Avg: {sum(lengths)/len(lengths):.1f}")
    print(f"Median: {sorted(lengths)[len(lengths)//2]}")
    print(f"Max: {max(lengths)}")
    for threshold in [5, 10, 20, 50]:
        cnt = sum(1 for l in lengths if l <= threshold)
        print(f"  <={threshold}: {cnt} ({cnt/len(lengths)*100:.1f}%)")
    cnt_long = sum(1 for l in lengths if l > 50)
    print(f"  >50: {cnt_long} ({cnt_long/len(lengths)*100:.1f}%)")

    # Punctuation
    punct = Counter()
    for t in texts:
        for ch in t:
            if ch in '。，！？、；：""''（）…—～~.!?,;:()【】':
                punct[ch] += 1
    print(f"\n=== Punctuation (top 15) ===")
    for p, c in punct.most_common(15):
        print(f"  '{p}': {c}")

    no_punct = sum(1 for t in texts if not re.search(r'[。，！？、；：…—～~.!?,;:]', t))
    print(f"No-punct: {no_punct} ({no_punct/len(texts)*100:.1f}%)")

    # Endings
    endings = Counter()
    for t in texts:
        if t.strip():
            endings[t.strip()[-1]] += 1
    print(f"\n=== Endings (top 15) ===")
    for e, c in endings.most_common(15):
        print(f"  '{e}': {c}")

    # Emoji
    emojis = Counter()
    for t in texts:
        for em in re.findall(r'\[([^\]]+?)\]', t.replace('\\[','[').replace('\\]',']')):
            emojis[em] += 1
    print(f"\n=== Emoji (top 15) ===")
    for e, c in emojis.most_common(15):
        print(f"  [{e}]: {c}")

    # High-freq short messages (exact match for short msgs)
    short_msgs = Counter(t for t in texts if len(t) <= 8)
    print(f"\n=== High-freq Short Messages (<=8 chars, top 30) ===")
    for w, c in short_msgs.most_common(30):
        print(f"  '{w}': {c}")

    # Sentence-initial patterns (first 2-3 chars)
    starters = Counter()
    for t in texts:
        t = t.strip()
        if len(t) >= 2:
            starters[t[:2]] += 1
    print(f"\n=== Sentence Starters (top 20) ===")
    for s, c in starters.most_common(20):
        print(f"  '{s}': {c}")

    # Consecutive burst analysis
    bursts = []
    burst = 1
    for i in range(1, len(msgs)):
        t1 = datetime.strptime(msgs[i-1][1], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.strptime(msgs[i][1], '%Y-%m-%d %H:%M:%S')
        if (t2 - t1).total_seconds() < 120:
            burst += 1
        else:
            if burst > 1:
                bursts.append(burst)
            burst = 1
    if burst > 1:
        bursts.append(burst)
    print(f"\n=== Burst Patterns ===")
    print(f"Bursts (2+ msgs <2min): {len(bursts)}")
    if bursts:
        print(f"Avg burst: {sum(bursts)/len(bursts):.1f}")
        print(f"Max burst: {max(bursts)}")
        bd = Counter(bursts)
        for s in sorted(bd.keys())[:8]:
            print(f"  {s}-msg burst: {bd[s]}x")

    # "哈" patterns (laughter)
    laugh = Counter()
    for t in texts:
        for m in re.findall(r'哈{2,}', t):
            laugh[m] += 1
    print(f"\n=== Laughter patterns ===")
    for l, c in sorted(laugh.items(), key=lambda x: -x[1])[:10]:
        print(f"  '{l}' ({len(l)}x哈): {c}")

    # Question marks usage
    q_msgs = [t for t in texts if '？' in t or '?' in t]
    print(f"\n=== Questions ===")
    print(f"Msgs with '?': {len(q_msgs)} ({len(q_msgs)/len(texts)*100:.1f}%)")

    # Monthly distribution
    monthly = Counter()
    for _, ts, _ in msgs:
        monthly[ts[:7]] += 1
    print(f"\n=== Monthly Distribution ===")
    for ym in sorted(monthly.keys()):
        print(f"  {ym}: {monthly[ym]}")

if __name__ == '__main__':
    main()
