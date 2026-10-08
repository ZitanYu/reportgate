"""Render pastes as HTML."""

import html
import re

LINK_RE = re.compile(r"https?://[^\s<>\"']+")


def render_paste(title, body):
    """Return an HTML fragment for a paste, escaping all user text."""
    safe_title = html.escape(title)
    safe_body = html.escape(body)
    linked = LINK_RE.sub(lambda m: '<a href="%s">%s</a>' % (m.group(0), m.group(0)), safe_body)
    return "<h1>%s</h1>\n<pre>%s</pre>" % (safe_title, linked)
