# cbot-tooling-how-i-choose (e.g., LinkedIn scraping)

## The order I use (simple + practical)

### 1) Check if it’s allowed / feasible
Before tools, I sanity-check:
- Is it behind a login/paywall (LinkedIn usually is)?
- Does it violate site rules / require bypassing security?
- Do you want **public-only** info or your logged-in feed?

If it needs login/cookies or “bypass,” I’ll stop and ask what you want instead (or ask you to attach a tab).

---

### 2) Check what tools I already have
I look at what’s available **right now**:
- Built-in tools: browser automation, `web_fetch`/`web_search`, file ops, cron, messaging
- Installed skills in the workspace (skills catalog)

If the task matches an existing skill, I use it. If not, I use the general tools.

---

### 3) Try the lowest-friction method first
- **Public page?** Try `web_fetch` (fast, no UI).
- **Needs JS / complex page?** Use the browser tool.
- **Logged-in LinkedIn view:** use the **Chrome Relay attached tab** (you attach the tab, then I can interact with it). That’s the only realistic way without storing cookies.

---

### 4) If I don’t have a tool, decide: quick helper vs real skill
- One-off: write a quick helper in `workspace/ops/`.
- Repeatable: build a proper skill in `skills/<name>/…`.

---

### 5) Do I figure it out proactively?
Yes, but only within reason:
- I’ll search the workspace for existing scripts/skills before asking you.
- I’ll try a quick test (`web_fetch` or browser open) to confirm.
- If it’s clearly blocked (login/bot protections), I’ll say so and suggest the best workaround.

---

## LinkedIn example (what I’d do)
- If you send a **public LinkedIn post URL**: try `web_fetch` first. If it fails, browser.
- If it’s your feed / private post: I’ll ask you to **attach the LinkedIn tab via Browser Relay**, then I can copy the post text or take screenshots and extract.

If you tell me what “scrape” means (text only? comments? author? timestamps?), I can choose the most reliable approach before we start.
