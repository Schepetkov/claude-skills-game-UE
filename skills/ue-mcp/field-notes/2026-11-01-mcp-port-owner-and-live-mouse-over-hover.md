---
symptom: an agent's MCP commands land in an editor it did not launch; a scripted hover state is gone by the time the screenshot is taken
engine: "5.8.1"
status: observed
date: 2026-11-01
source: one session verifying a board-hover highlight in PIE while another editor of the same project was opened by someone else
---
- **Two editors of the same project race for the port.** The agent launched an editor; six seconds later another one
  (same `.uproject`, different command line) was started by someone else. The second bound `:8000` first, the agent's
  own editor came up without a server, and every `call_tool` (StartPIE included) went into the other person's editor.
  After launching, check that the listener belongs to the process you started:
  `Get-NetTCPConnection -LocalPort 8000 -State Listen` → `OwningProcess` == your PID. If not, decide before any
  exclusive operation (PIE, load level): it is someone else's editor.
- **Two editors of one project write two logs**: the second one gets `<Project>_2.log`. Grep the log of the editor
  that owns the port (newest by mtime), not the default name — the default one stopped updating and looked like "the
  command did nothing".
- **A real mouse over the PIE viewport overrides a scripted hover.** Someone moving the mouse across the viewport
  re-traces the hovered cell every frame, so `hover x,y` followed by a separate capture call shot a different cell.
  Send select + hover + camera + capture in ONE console batch (the same tick), and confirm in the log that the hovered
  cell at capture time is the one you asked for.
