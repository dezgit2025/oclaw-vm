import datetime
from collections import Counter

LOGFILE = '/home/desazure/.openclaw/workspace/logs/model_routing.log'


def parse_log_line(line):
    parts = line.strip().split(' - ')
    if len(parts) < 3:
        return None
    try:
        timestamp_str = parts[0]
        model_part = [p for p in parts if p.startswith('model:')][0]
        model = model_part.split(':', 1)[1]
        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        return timestamp, model
    except Exception:
        return None


def report_for_today():
    today = datetime.datetime.utcnow().date()
    counts = Counter()
    total = 0
    with open(LOGFILE, 'r') as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed is None:
                continue
            timestamp, model = parsed
            if timestamp.date() == today:
                total += 1
                counts[model] += 1
    if total == 0:
        print('No routing log entries for today')
        return
    print(f'Model routing summary for {today.isoformat()}:')
    for model, count in counts.items():
        pct = count / total * 100
        print(f'- {model}: {count} requests ({pct:.1f}%)')


if __name__ == '__main__':
    report_for_today()
