from datetime import datetime, timedelta, timezone

MAX_LENGTH = 2000

SHA_TZ = timezone(timedelta(hours=8))


def build_table_of_contents():
    return {"type": "table_of_contents", "table_of_contents": {"color": "default"}}


def build_heading(level, text):
    heading = f"heading_{min(max(level, 1), 3)}"
    return {
        "type": heading,
        heading: {
            "rich_text": [{"type": "text", "text": {"content": text[:MAX_LENGTH]}}],
            "color": "default",
            "is_toggleable": False,
        },
    }


def build_callout(text, style=0, color_style=0, is_review=False):
    if is_review:
        emoji = "✍️"
    elif style == 0:
        emoji = "\U0001f4a1"
    elif style == 1:
        emoji = "⭐"
    else:
        emoji = "〰️"

    color = "default"
    if color_style == 1:
        color = "red"
    elif color_style == 2:
        color = "purple"
    elif color_style == 3:
        color = "blue"
    elif color_style == 4:
        color = "green"
    elif color_style == 5:
        color = "yellow"

    return {
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text[:MAX_LENGTH]}}],
            "color": color,
            "icon": {"emoji": emoji},
        },
    }


def build_quote(text):
    return {
        "type": "quote",
        "quote": {
            "rich_text": [{"type": "text", "text": {"content": text[:MAX_LENGTH]}}],
            "color": "default",
        },
    }


def timestamp_to_date(ts):
    if not ts:
        return None
    dt = datetime.fromtimestamp(ts, tz=SHA_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate(text, max_len=MAX_LENGTH):
    if not text:
        return ""
    return text[:max_len]
