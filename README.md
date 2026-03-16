# Claude Export Session

Claude Code stores conversations as raw JSONL files — machine-readable but painful for humans. Messages, tool calls, tool results, and system noise are all flattened into one stream with no visual distinction. Trying to review a session means scrolling through walls of JSON where user prompts, assistant responses, file contents, and internal tool plumbing all look the same. Tool results show up labeled as "user" messages. Code blocks have no syntax highlighting. Large outputs aren't collapsible. It's hard to find what you're looking for, and impossible to share with anyone who wasn't in the conversation.

This skill turns those raw JSONL logs into clean, readable HTML reports with a dark theme, color-coded roles, syntax-highlighted code, collapsible sections, and expandable diffs — making it easy to review, share, or archive your Claude Code sessions.

## Features

- Dark Catppuccin Mocha themed HTML output
- Syntax highlighting via highlight.js (loaded from CDN)
- Collapsible large code blocks (12+ lines)
- Expandable Write/Edit tool blocks with diff views
- Tool results distinguished from user messages
- Styled Q&A formatting for AskUserQuestion results
- Word-wrapped content in collapsible sections
- Zero dependencies — uses Python stdlib only (optional `markdown` for richer HTML)

## Installation

Clone or copy the repo into your Claude Code skills directory:

```bash
# Option 1: Clone directly into skills dir
git clone https://github.com/SanderBuruma/claude-export-session.git ~/.claude/skills/export-session

# Option 2: Copy manually
cp -r claude-export-session ~/.claude/skills/export-session
```

The resulting structure should be:
```
~/.claude/skills/export-session/
├── SKILL.md
├── README.md
└── scripts/
    └── export_session.py
```

No `pip install`, no venv, no dependencies required. Just Python 3.x.

Optionally, for slightly better HTML rendering of markdown content:
```bash
pip install markdown
```

## Usage

### As a Claude Code skill

Say `/export-session` or use natural language like "export this session" or "save this chat".

### Standalone

```bash
python ~/.claude/skills/export-session/scripts/export_session.py <path-to-session.jsonl>
```

Session JSONL files are located at:
```
~/.claude/projects/<project-dir>/<session-id>.jsonl
```

## Output

Reports are saved to `~/.claude/custom-reports/{date}-{slug}/`:
- `session.md` — clean Markdown
- `session.html` — styled HTML with syntax highlighting

## Security Warning

After export, an automated Haiku 4.5 security scan reads the generated Markdown and flags API keys, tokens, credentials, internal IPs, connection strings, and other secrets. Flagged content is auto-redacted in both the `.md` and `.html` outputs before you're offered to open or share them.

Automated scanning may miss context-dependent secrets — always do a manual review before sharing exported reports publicly or uploading them to repositories.

## Platform support

Works on Windows, macOS, and Linux. The output directory is auto-resolved from `$USERPROFILE` (Windows) or `$HOME` (macOS/Linux). Override with `CLAUDE_CONFIG_DIR` env var if your `.claude` directory is in a non-standard location.
