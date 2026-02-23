// before_agent_start hook: memory recall injection
// Queries Azure AI Search via smart_extractor.py recall command
// Falls back gracefully: Azure -> SQLite -> skip

const { execSync } = require("child_process");
const path = require("path");

const SKILL_DIR = path.join(
  process.env.HOME,
  ".openclaw/workspace/skills/clawbot-memory"
);
const VENV_PYTHON = path.join(SKILL_DIR, ".venv/bin/python3");
const EXTRACTOR = path.join(SKILL_DIR, "smart_extractor.py");
const TIMEOUT_MS = 4000; // 4s total budget (includes python startup)

module.exports = async function (event, ctx) {
  try {
    // Extract last user message
    const messages = event.messages || [];
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser || !lastUser.content) return;

    const query =
      typeof lastUser.content === "string"
        ? lastUser.content
        : Array.isArray(lastUser.content)
          ? lastUser.content
              .filter((p) => p.type === "text")
              .map((p) => p.text)
              .join(" ")
          : "";

    if (!query || query.length < 3) return;

    // Truncate query to first 200 chars for search
    const truncated = query.substring(0, 200);

    // Shell out to smart_extractor.py recall
    // Note: recall outputs <clawbot_context> tags already, no extra wrapping needed
    const cmd = `${VENV_PYTHON} ${EXTRACTOR} recall "${truncated.replace(/"/g, '\\"')}" -k 5 2>/dev/null`;

    const output = execSync(cmd, {
      timeout: TIMEOUT_MS,
      encoding: "utf-8",
      env: {
        ...process.env,
        AZURE_SEARCH_ENDPOINT:
          process.env.AZURE_SEARCH_ENDPOINT ||
          "https://oclaw-search.search.windows.net",
        AZURE_OPENAI_ENDPOINT:
          process.env.AZURE_OPENAI_ENDPOINT ||
          "https://oclaw-openai.openai.azure.com/",
        AZURE_OPENAI_CHAT_ENDPOINT:
          process.env.AZURE_OPENAI_CHAT_ENDPOINT ||
          "https://pitchbook-resource.cognitiveservices.azure.com/",
      },
    }).trim();

    if (output && output.length > 10) {
      return {
        prependContext: output,
      };
    }
  } catch (err) {
    // Graceful degradation: timeout, missing deps, or any error -> skip
    if (err.status !== undefined) {
      // execSync non-zero exit — extractor had an error, skip silently
    } else if (err.killed) {
      // timeout — skip silently
      console.warn("[clawbot-memory] Recall timed out, skipping");
    } else {
      console.warn("[clawbot-memory] Hook error:", err.message);
    }
  }
};
