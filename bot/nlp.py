import re
from datetime import datetime, timedelta

def extract_hours(text):
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)', text, re.I)
    return [float(m) for m in matches]

def extract_date(text):
    text = text.lower()

    if "today" in text:
        return datetime.now().date()
    if "yesterday" in text:
        return datetime.now().date() - timedelta(days=1)

    # TODO: weekday + explicit date parsing
    return datetime.now().date()

def extract_projects(text):
    parts = re.split(r'\bon\b|\bfor\b', text, flags=re.I)
    if len(parts) > 1:
        return parts[1].split()[0]  # first token after 'on'
    return "General"

def extract_task_desc(text):
    return text  # later we'll improve this

def split_multiple_tasks(text):
    segments = re.split(r'\band\b|,', text)
    return [seg.strip() for seg in segments if len(seg.strip()) > 3]
