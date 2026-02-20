import { withClient, extractText } from "./_client.mjs";

const url = process.argv[2];
if (!url) {
  console.error('Usage: mslearn_fetch.mjs "<url>"');
  process.exit(2);
}

const out = await withClient(async (client) => {
  return await client.callTool({
    name: "microsoft_docs_fetch",
    arguments: { url },
  });
});

const parsed = extractText(out);
console.log(JSON.stringify(parsed, null, 2));
