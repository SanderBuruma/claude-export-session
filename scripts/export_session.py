#!/usr/bin/env python3
"""Export a Claude Code JSONL session log to Markdown + styled HTML.

Usage:
    python export-session-md.py <session.jsonl>

Outputs both .md and .html to ~/.claude/custom-reports/{session-name}/
Session name is derived from the first user message or falls back to session ID.
"""

import json
import os
import sys
import re
import html as html_mod
from pathlib import Path
from datetime import datetime

try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

def _get_reports_dir():
    """Resolve reports directory, works on Windows, macOS, and Linux."""
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if claude_dir:
        return Path(claude_dir) / "custom-reports"
    if sys.platform == "win32":
        home = os.environ.get("USERPROFILE", Path.home())
    else:
        home = Path.home()
    return Path(home) / ".claude" / "custom-reports"

REPORTS_DIR = _get_reports_dir()

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: #1e1e2e;
    --surface: #282838;
    --text: #cdd6f4;
    --subtext: #a6adc8;
    --blue: #89b4fa;
    --green: #a6e3a1;
    --peach: #fab387;
    --mauve: #cba6f7;
    --red: #f38ba8;
    --teal: #94e2d5;
    --overlay: #45475a;
    --user-bg: #2a2a3c;
    --assistant-bg: #1e1e2e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}
  h1 {{
    color: var(--mauve);
    border-bottom: 2px solid var(--overlay);
    padding-bottom: 0.5rem;
    margin-bottom: 0.3rem;
    font-size: 1.6rem;
  }}
  .meta {{
    color: var(--subtext);
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
  }}
  .message {{
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
  }}
  .message.user {{
    background: var(--user-bg);
    border-left: 3px solid var(--blue);
  }}
  .message.assistant {{
    background: var(--assistant-bg);
    border-left: 3px solid var(--green);
  }}
  .role {{
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
  }}
  .role.user {{ color: var(--blue); }}
  .role.assistant {{ color: var(--green); }}
  .role.tool-result {{ color: var(--subtext); }}
  .message.tool-result {{
    background: var(--surface);
    border-left: 3px solid var(--overlay);
  }}
  .timestamp {{
    color: var(--subtext);
    font-weight: 400;
    font-size: 0.75rem;
    margin-left: 0.5rem;
  }}
  .content {{ font-size: 0.95rem; }}
  .content p {{ margin-bottom: 0.6rem; }}
  .content h1, .content h2, .content h3 {{
    color: var(--peach);
    margin: 0.8rem 0 0.4rem;
    font-size: 1.1rem;
  }}
  .content h1 {{ font-size: 1.25rem; }}
  .content ul, .content ol {{
    margin: 0.4rem 0 0.6rem 1.5rem;
  }}
  .content li {{ margin-bottom: 0.2rem; }}
  .content code {{
    background: var(--overlay);
    padding: 0.15em 0.4em;
    border-radius: 3px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 0.88em;
  }}
  .content pre {{
    background: var(--surface);
    border: 1px solid var(--overlay);
    border-radius: 6px;
    padding: 0.8rem 1rem;
    overflow-x: auto;
    margin: 0.5rem 0;
  }}
  .content pre code {{
    background: none;
    padding: 0;
    font-size: 0.85em;
  }}
  blockquote {{
    border-left: 3px solid var(--teal);
    padding: 0.3rem 0.8rem;
    margin: 0.5rem 0;
    background: rgba(148, 226, 213, 0.05);
    color: var(--teal);
    font-size: 0.88rem;
  }}
  blockquote strong {{ color: var(--peach); }}
  blockquote code {{
    background: var(--overlay);
    padding: 0.1em 0.3em;
    border-radius: 3px;
  }}
  details {{
    margin: 0.5rem 0;
    border: 1px solid var(--overlay);
    border-radius: 6px;
    overflow: hidden;
  }}
  summary {{
    padding: 0.4rem 0.8rem;
    background: var(--surface);
    cursor: pointer;
    color: var(--subtext);
    font-size: 0.85rem;
  }}
  details pre {{
    margin: 0;
    border: none;
    border-radius: 0;
    border-top: 1px solid var(--overlay);
    white-space: pre-wrap;
    word-break: break-word;
  }}
  .qa-block {{
    background: var(--surface);
    border-radius: 6px;
    padding: 0.6rem 1rem;
    margin: 0.5rem 0;
  }}
  .qa-pair {{
    margin-bottom: 0.5rem;
  }}
  .qa-pair:last-child {{ margin-bottom: 0; }}
  .qa-q {{ color: var(--teal); font-weight: 600; }}
  .qa-a {{ color: var(--green); margin-left: 0.5rem; }}
  a {{ color: var(--blue); }}
  strong {{ color: var(--peach); }}
  em {{ color: var(--subtext); }}
  hr {{
    border: none;
    border-top: 1px solid var(--overlay);
    margin: 1.5rem 0;
  }}
  table {{
    border-collapse: collapse;
    margin: 0.5rem 0;
    width: 100%;
  }}
  th, td {{
    border: 1px solid var(--overlay);
    padding: 0.4rem 0.7rem;
    text-align: left;
  }}
  th {{ background: var(--surface); color: var(--peach); }}
  /* highlight.js overrides for Catppuccin consistency */
  .hljs {{ background: var(--surface) !important; color: var(--text) !important; }}
  .hljs-keyword, .hljs-selector-tag {{ color: var(--mauve) !important; }}
  .hljs-string, .hljs-addition {{ color: var(--green) !important; }}
  .hljs-number, .hljs-literal {{ color: var(--peach) !important; }}
  .hljs-comment, .hljs-quote {{ color: var(--subtext) !important; font-style: italic; }}
  .hljs-attr, .hljs-selector-class {{ color: var(--blue) !important; }}
  .hljs-title, .hljs-section {{ color: var(--peach) !important; }}
  .hljs-built_in {{ color: var(--teal) !important; }}
  .hljs-type, .hljs-class {{ color: var(--peach) !important; }}
  .hljs-variable, .hljs-template-variable {{ color: var(--red) !important; }}
  .hljs-symbol, .hljs-bullet {{ color: var(--green) !important; }}
  .hljs-deletion {{ color: var(--red) !important; }}
  .hljs-name, .hljs-tag {{ color: var(--blue) !important; }}
  .hljs-property {{ color: var(--blue) !important; }}
  .hljs-punctuation {{ color: var(--subtext) !important; }}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/base16/catppuccin-mocha.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
</head>
<body>
<h1>{title}</h1>
<div class="meta">{meta}</div>
{body}
<script>
hljs.highlightAll();
// Wrap large pre/code blocks in collapsible details
document.querySelectorAll('pre').forEach(pre => {{
  const lines = pre.textContent.split('\\n').length;
  if (lines < 12) return;
  // Skip if already inside a details element
  if (pre.closest('details')) return;
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  const code = pre.querySelector('code');
  const lang = code ? (code.className.match(/language-(\\w+)/)||[])[1]||'' : '';
  summary.textContent = lang ? lang + ' \u2014 ' + lines + ' lines' : lines + ' lines';
  pre.parentNode.insertBefore(details, pre);
  details.appendChild(summary);
  details.appendChild(pre);
}});
</script>
</body>
</html>
"""


def extract_text_content(content):
    """Extract text from message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    name = block.get("name", "unknown")
                    inp = block.get("input", {})
                    parts.append(format_tool_use(name, inp))
                elif block.get("type") == "tool_result":
                    text = block.get("content", "")
                    if isinstance(text, list):
                        text = "\n".join(
                            b.get("text", "") for b in text if isinstance(b, dict)
                        )
                    if text and not text.startswith(("The user doesn't want", "[Request interrupted")):
                        # Format Q&A pairs from AskUserQuestion as styled Q/A
                        if "answered your questions:" in text:
                            qa_pairs = re.findall(r'"([^"]+?)"="([^"]*?)"', text)
                            if qa_pairs:
                                qa_html = "\n".join(
                                    f'<div class="qa-pair"><span class="qa-q">Q: {q}</span><br>'
                                    f'<span class="qa-a">A: {a}</span></div>'
                                    for q, a in qa_pairs
                                )
                                parts.append(f'<div class="qa-block">{qa_html}</div>')
                                continue
                        parts.append(f"<details><summary>Tool result</summary>\n\n```\n{text}\n```\n</details>")
        return "\n\n".join(p for p in parts if p)
    return ""


def format_tool_use(name, inp):
    """Format a tool use block concisely."""
    if name == "Read":
        return f"> **Read** `{inp.get('file_path', '?')}`"
    if name == "Write":
        path = inp.get("file_path", "?")
        content = inp.get("content", "")
        lines = content.count("\n") + 1
        ext = Path(path).suffix.lstrip(".") or "text"
        return f"<details><summary><strong>Write</strong> <code>{path}</code> ({lines} lines)</summary>\n\n```{ext}\n{content}\n```\n</details>"
    if name == "Edit":
        path = inp.get("file_path", "?")
        old = inp.get("old_string", "")
        new = inp.get("new_string", "")
        if old or new:
            ext = Path(path).suffix.lstrip(".") or "text"
            diff_lines = []
            for line in old.splitlines():
                diff_lines.append(f"- {line}")
            for line in new.splitlines():
                diff_lines.append(f"+ {line}")
            diff_text = "\n".join(diff_lines)
            return f"<details><summary><strong>Edit</strong> <code>{path}</code></summary>\n\n```diff\n{diff_text}\n```\n</details>"
        return f"> **Edit** `{path}`"
    if name in ("Glob", "Grep"):
        return f"> **{name}** `{inp.get('pattern', '?')}`"
    if name == "Bash":
        cmd = inp.get("command", "?")
        return f"> **Bash** `{cmd}`"
    if name == "Agent":
        return f"> **Agent** _{inp.get('description', '?')}_"
    if name == "Skill":
        return f"> **Skill** `{inp.get('skill', '?')}`"
    summary = json.dumps(inp, ensure_ascii=False, indent=2)
    return f"> **{name}**\n\n```json\n{summary}\n```"


def parse_session(jsonl_path):
    """Parse JSONL and yield (role, timestamp, text) tuples."""
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = entry.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            msg = entry.get("message", {})
            role = msg.get("role", msg_type)
            content = msg.get("content", "")
            ts = entry.get("timestamp", "")

            # Detect tool_result messages: user messages with only tool_result blocks
            if role == "user" and isinstance(content, list):
                has_real_text = any(
                    isinstance(b, dict) and b.get("type") == "text"
                    and not b.get("text", "").startswith(("<system-reminder>", "[Request interrupted", "The user doesn't want"))
                    for b in content
                )
                has_tool_result = any(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in content
                )
                if has_tool_result and not has_real_text:
                    role = "tool_result"

            text = extract_text_content(content)
            if not text:
                continue
            if text.startswith(("[Request interrupted", "The user doesn't want")):
                continue

            yield role, ts, text


def format_timestamp(ts_str):
    """Format ISO timestamp to readable form."""
    if not ts_str:
        return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return ""


def get_session_date(jsonl_path):
    """Get date from first timestamp in session."""
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("timestamp", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return dt.strftime("%Y-%m-%d")
            except (json.JSONDecodeError, ValueError):
                continue
    return "unknown-date"


def derive_session_name(jsonl_path):
    """Derive a readable folder name from the first user message."""
    session_id = Path(jsonl_path).stem
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "user":
                continue
            msg = entry.get("message", {})
            content = msg.get("content", "")
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block["text"]
                        break
            if text and not text.startswith(("[Request interrupted", "The user doesn't want")):
                # Slugify first ~60 chars
                slug = text[:60].strip().lower()
                slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
                if slug:
                    date = get_session_date(jsonl_path)
                    return f"{date}-{slug}"
    date = get_session_date(jsonl_path)
    return f"{date}-{session_id[:8]}"


def to_markdown(jsonl_path):
    """Convert session to markdown string."""
    path = Path(jsonl_path)
    lines = []
    lines.append("# Claude Code Session")
    lines.append(f"*Source: `{path.name}`*\n")
    lines.append("---\n")

    prev_role = None
    for role, ts, text in parse_session(jsonl_path):
        time_str = format_timestamp(ts)
        time_suffix = f" *({time_str})*" if time_str else ""

        if role == "tool_result":
            lines.append(f"## Tool Result{time_suffix}\n")
            lines.append(text)
            lines.append("")
        elif role == "user":
            lines.append(f"## User{time_suffix}\n")
            lines.append(text)
            lines.append("")
        elif role == "assistant":
            if prev_role != "assistant":
                lines.append(f"## Assistant{time_suffix}\n")
            lines.append(text)
            lines.append("")
        prev_role = role

    return "\n".join(lines)


def md_to_html_body(md_text):
    """Convert markdown to HTML body content."""
    if HAS_MARKDOWN:
        return md_lib.markdown(
            md_text,
            extensions=["fenced_code", "tables", "nl2br"],
        )
    # Fallback: basic conversion without the markdown library
    h = html_mod.escape(md_text)
    # Code blocks
    h = re.sub(r'```(\w*)\n(.*?)```', lambda m: f'<pre><code>{m.group(2)}</code></pre>', h, flags=re.DOTALL)
    # Inline code
    h = re.sub(r'`([^`]+)`', r'<code>\1</code>', h)
    # Bold
    h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', h)
    # Italic
    h = re.sub(r'\*(.+?)\*', r'<em>\1</em>', h)
    # Headers
    h = re.sub(r'^### (.+)$', r'<h3>\1</h3>', h, flags=re.MULTILINE)
    h = re.sub(r'^## (.+)$', r'<h2>\1</h2>', h, flags=re.MULTILINE)
    h = re.sub(r'^# (.+)$', r'<h1>\1</h1>', h, flags=re.MULTILINE)
    # Blockquotes
    h = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', h, flags=re.MULTILINE)
    # HR
    h = re.sub(r'^---+$', '<hr>', h, flags=re.MULTILINE)
    # Paragraphs
    h = re.sub(r'\n\n+', '</p>\n<p>', h)
    h = f'<p>{h}</p>'
    return h


def to_html(jsonl_path):
    """Convert session to styled HTML."""
    path = Path(jsonl_path)
    date = get_session_date(jsonl_path)
    parts = []

    prev_role = None
    for role, ts, text in parse_session(jsonl_path):
        time_str = format_timestamp(ts)
        ts_html = f'<span class="timestamp">{time_str}</span>' if time_str else ""

        if role == "tool_result":
            content_html = md_to_html_body(text)
            parts.append(
                f'<div class="message tool-result">'
                f'<div class="role tool-result">Tool Result {ts_html}</div>'
                f'<div class="content">{content_html}</div>'
                f'</div>'
            )
        elif role == "user":
            content_html = md_to_html_body(text)
            parts.append(
                f'<div class="message user">'
                f'<div class="role user">User {ts_html}</div>'
                f'<div class="content">{content_html}</div>'
                f'</div>'
            )
        elif role == "assistant":
            content_html = md_to_html_body(text)
            if prev_role != "assistant":
                parts.append(
                    f'<div class="message assistant">'
                    f'<div class="role assistant">Assistant {ts_html}</div>'
                    f'<div class="content">{content_html}</div>'
                    f'</div>'
                )
            else:
                parts.append(
                    f'<div class="message assistant">'
                    f'<div class="content">{content_html}</div>'
                    f'</div>'
                )
        prev_role = role

    title = f"Claude Code Session - {date}"
    meta = f"Source: <code>{path.name}</code>"
    body = "\n".join(parts)

    return HTML_TEMPLATE.format(title=title, meta=meta, body=body)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    jsonl_path = sys.argv[1]
    if not Path(jsonl_path).exists():
        print(f"Error: {jsonl_path} not found", file=sys.stderr)
        sys.exit(1)

    session_name = derive_session_name(jsonl_path)
    out_dir = REPORTS_DIR / session_name
    out_dir.mkdir(parents=True, exist_ok=True)

    md_text = to_markdown(jsonl_path)
    md_path = out_dir / "session.md"
    md_path.write_text(md_text, encoding="utf-8")

    html_text = to_html(jsonl_path)
    html_path = out_dir / "session.html"
    html_path.write_text(html_text, encoding="utf-8")

    print(f"Exported to {out_dir}")
    print(f"  {md_path}")
    print(f"  {html_path}")


if __name__ == "__main__":
    main()
