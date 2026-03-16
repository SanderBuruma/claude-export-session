# Claude Export Session

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that exports JSONL session logs to clean Markdown and styled HTML reports.

## Features

- Dark Catppuccin Mocha themed HTML output
- Syntax highlighting via highlight.js
- Collapsible large code blocks (12+ lines)
- Expandable Write/Edit tool blocks with diff views
- Tool results distinguished from user messages
- Styled Q&A formatting for AskUserQuestion results
- Word-wrapped content in collapsible sections

## Installation

Copy or symlink the `export-session` folder into your Claude Code skills directory:

```
~/.claude/skills/export-session/
├── SKILL.md
├── README.md
└── scripts/
    └── export_session.py
```

## Usage

### As a Claude Code skill

Say `/export-session` or use natural language like "export this session" or "save this chat".

### Standalone

```bash
python scripts/export_session.py <path-to-session.jsonl>
```

Session JSONL files are located at:
```
~/.claude/projects/<project-dir>/<session-id>.jsonl
```

## Output

Reports are saved to `~/.claude/custom-reports/{date}-{slug}/`:
- `session.md` — clean Markdown
- `session.html` — styled HTML with syntax highlighting

## Dependencies

- Python 3.x
- Optional: `markdown` library for better HTML conversion (falls back to regex-based conversion)
