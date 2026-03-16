---
name: export-session
description: Export a Claude Code conversation session to clean Markdown and styled HTML reports. Use this skill whenever the user asks to export, save, or share a conversation, wants a readable version of a session log, asks for a conversation report, or says things like "export this session", "save this chat", "make this conversation readable", "generate a report of our conversation". Also trigger when the user references session JSONL files and wants them converted to a human-readable format.
---

# Export Session

Converts Claude Code JSONL session logs into clean Markdown and a dark-themed HTML report. Both files are saved to `~/.claude/custom-reports/{date}-{slug}/`.

## How it works

The bundled script at `scripts/export_session.py` (relative to this skill) handles all conversion. It:
- Parses the JSONL session log
- Extracts user and assistant messages with timestamps
- Formats tool uses as concise blockquotes (Read, Write, Edit, Bash, etc.)
- Wraps tool results in collapsible `<details>` blocks
- Skips system noise (rejected tool uses, interrupts, progress entries)
- Derives a folder name from the session date + first user message
- Outputs both `session.md` and `session.html` (dark Catppuccin-style theme)

## Usage

Run the script with the path to a JSONL session file:

```bash
python <skill-path>/scripts/export_session.py <path-to-session.jsonl>
```

### Finding session files

Session JSONL files live at:
```
~/.claude/projects/<project-dir>/<session-id>.jsonl
```

To find the right file:
- List recent sessions: `ls -lt ~/.claude/projects/<project-dir>/*.jsonl | head -5`
- The current session ID is visible in the session log path

### Exporting the current session

The current conversation's session ID can be found by listing the most recently modified JSONL in the relevant project directory. Export it the same way.

### Output location

Reports are saved to:
```
~/.claude/custom-reports/{date}-{slugified-first-message}/
  session.md
  session.html
```

After export, offer to open the HTML in the browser (`start` on Windows, `open` on macOS, `xdg-open` on Linux).

## Security Audit

The export script automatically runs a Haiku 4.5 security scan after generating the reports. It invokes `claude --dangerously-skip-permissions --print --model haiku` to scan `session.md` for API keys, tokens, credentials, internal IPs, connection strings, private keys, and email addresses. Flagged content is auto-redacted (replaced with `[REDACTED]`) in both `session.md` and `session.html` (including HTML-escaped variants). The audit is skipped gracefully if the `claude` CLI is not available on PATH.

## Dependencies

- Python 3.x (stdlib only — no pip install required)
- Optional: `claude` CLI on PATH — enables the automated Haiku 4.5 security audit
- Optional: `markdown` library (`pip install markdown`) for better HTML conversion; falls back to built-in regex conversion if unavailable
