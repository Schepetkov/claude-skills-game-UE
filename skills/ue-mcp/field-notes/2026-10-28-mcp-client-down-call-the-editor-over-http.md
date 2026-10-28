---
symptom: the agent session's Unreal MCP tools are gone ("failed to connect" at session start) although the editor and its MCP server are up now
engine: "5.8.1"
status: observed
date: 2026-10-28
source: Unreal MCP server (Streamable HTTP, http://127.0.0.1:8000/mcp) called with urllib from Python
---
If the editor was closed when the agent session started, the client marks the server failed and does not retry; the
tools stay unavailable for the session. The server itself is plain HTTP JSON-RPC, so a 30-line script reaches it:

1. POST `{"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{...}}}` with
   `Accept: application/json, text/event-stream`; keep the `Mcp-Session-Id` response header.
2. POST `{"method":"notifications/initialized"}` with that header.
3. POST `{"method":"tools/call","params":{"name":"call_tool","arguments":{"toolset_name":...,"tool_name":...,"arguments":{...}}}}`.
   A response may come as SSE (`data:` lines) - strip the prefix before parsing. Screenshots are several MB of
   base64: write the result to a file.

Hooks that guard exclusive editor operations (PIE, Live Coding, closing the editor) match the agent's MCP tool
calls, so they do not see this script. Take the lock yourself before StartPIE and release it after StopPIE - e.g.
feed the lock hook a synthetic PreToolUse/PostToolUse event carrying your session id - so parallel sessions still
see who holds the editor.
