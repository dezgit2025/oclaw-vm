import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const url = process.argv[2] || "https://learn.microsoft.com/api/mcp";

const client = new Client(
  { name: "openclaw-mslearn", version: "0.1.0" },
  { capabilities: {} }
);

const transport = new StreamableHTTPClientTransport(new URL(url));

try {
  await client.connect(transport);
  const tools = await client.listTools();
  console.log(JSON.stringify(tools, null, 2));
} finally {
  await client.close();
}
