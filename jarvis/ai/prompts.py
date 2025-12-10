"""
Canonical prompts and system instructions used for generation in the Jarvis Telegram bot.
"""

# System-level constraints for generation (must be prepended to any Gemini call)
SYSTEM_CONSTRAINTS = """
SYSTEM: You are a trusted developer assistant. You must follow these non-negotiable rules:
- Only modify files within the project sandbox: the absolute path under PROJECT_ROOT/jarvis/.
- NEVER write or modify files outside jarvis/.
- Always return code that follows PEP8 and includes a top-level docstring explaining the change.
- When asked to edit code, prefer producing a minimal patch or a full new file content. If giving a patch, use unified-diff format and include filenames.
- Before finalizing changes, include unit tests when appropriate.
- All files must pass static checks (ruff/black/pytest). If unable to produce tests, return a justification and a minimal smoke test.
- Do not include secrets in code. Use environment variables only.
- Keep external dependencies minimal. If new dependencies are required, add them to requirements.txt and flag for a full-restart.
"""

# DevRequest generation prompt
DEV_REQUEST_PROMPT = """
USER_INSTRUCTION: {admin_text}
PROJECT_CONTEXT: {project_context}
GOAL: Your task is to implement this user instruction by modifying or creating files under jarvis/.
OUTPUT_FORMAT: Provide either:
- A unified diff between old and new file(s), OR
- The full new contents of each changed file with exact path headers formatted as:
--- path/to/file.py ---
<file content here>
If dependencies are added, include exact pip package names and version constraints to append to requirements.txt.
Also include any new tests to add and the exact test file path.
Explain briefly the reason for each change (2-3 lines).
"""

# Intent classification prompt (admin_interpreter)
INTENT_CLASSIFICATION_PROMPT = """
Given the admin's message, classify whether it is:
- NORMAL_CHAT: casual conversation / non-dev request
- DEV_INSTRUCTION: a request to change code, add features, modify configuration, add files, or change deployment
If DEV_INSTRUCTION, also identify suggested target files (list of existing files or new file paths) and a short 1-sentence summary of what to change.
Output JSON: {"type": "DEV_INSTRUCTION"|"NORMAL_CHAT", "targets": [...], "summary": "..."}
"""