import { withClient, extractText } from "./_client.mjs";

const query = process.argv.slice(2).join(" ").trim();
if (!query) {
  console.error('Usage: mslearn_code_search.mjs "<query>"');
  process.exit(2);
}

const out = await withClient(async (client) => {
  return await client.callTool({
    name: "microsoft_code_sample_search",
    arguments: { query },
  });
});

const parsed = extractText(out);
console.log(JSON.stringify(parsed, null, 2));
