import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

export const DEFAULT_URL = "https://learn.microsoft.com/api/mcp";

export async function withClient(fn, url = DEFAULT_URL) {
  const client = new Client(
    { name: "openclaw-mslearn", version: "0.1.0" },
    { capabilities: {} }
  );
  const transport = new StreamableHTTPClientTransport(new URL(url));
  await client.connect(transport);
  try {
    return await fn(client);
  } finally {
    await client.close();
  }
}

export function extractText(result) {
  // result.content is an array of {type:'text', text:'...json...'}
  const parts = (result && result.content) || [];
  const texts = parts
    .filter((p) => p && p.type === "text" && typeof p.text === "string")
    .map((p) => p.text);
  if (!texts.length) return null;
  // Many MCP servers return JSON as a string.
  const joined = texts.join("\n");
  try {
    return JSON.parse(joined);
  } catch {
    return joined;
  }
}
