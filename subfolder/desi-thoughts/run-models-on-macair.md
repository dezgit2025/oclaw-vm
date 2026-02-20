# Run models on a MacBook Air (M4, 32GB) — notes

**Last updated (UTC):** 2026-02-07 18:09

## What we were trying to solve
You wanted a setup for **coding + chat + tool-calling** on a **2026 MacBook Air M4 with 32GB unified memory**, while keeping **~8GB free** so you can still run other work (e.g., Claude Code, editor, browser).

## Key concepts (simple)
### “Open-weight”
- **Open-weight** means you can **download the trained model weights** (the parameter files) and **run the model locally**.
- It **does not automatically** mean: unrestricted use, open training data, or no license constraints.

### Why Kimi K2.5 is hard to run locally on a MacBook Air
- Kimi K2.5 is described as a very large **MoE** model (huge total params; large activated params).
- Even if there are **quantized** community builds, it’s generally **not practical** for fast, comfortable interactive use on a MacBook Air—especially if you want to keep ~8GB RAM headroom.

## “Kimi-like” local alternatives (realistic on a laptop)
Rule of thumb we used:
- Prefer **7B–8B instruct** models at **4-bit quantization**, with **~8k context**.
- 13B–14B may work but usually becomes noticeably slower/tighter on memory.

### Three suggestions (quantized)
1) **Qwen2.5 7B Instruct** (best overall balance)
2) **Llama 3.1 8B Instruct** (stable general assistant + solid ecosystem)
3) **DeepSeek-Coder 6.7B Instruct** (coding-focused)

## Which runner to use on macOS (pros/cons)
### Ollama (recommended)
**Pros**
- Easiest install + model management
- Simple local HTTP API (good for tool-calling / agent loops)
- Good Apple Silicon performance with quantized models

**Cons**
- Less low-level control than raw llama.cpp

### llama.cpp (power user)
**Pros**
- Maximum control over performance/memory knobs
- Very transparent + scriptable

**Cons**
- More DIY: builds, flags, model file management

### LM Studio (GUI)
**Pros**
- Easiest to browse/try lots of models via UI

**Cons**
- Heavier footprint; less automation-oriented than Ollama

## Chosen path for you
You chose:
- Runner: **Ollama**
- Model: **Qwen2.5 7B Instruct**
- Target settings: **4-bit** quant, **~8k context**, aim for **~8GB free**

## Suggested Ollama setup (commands)
> Note: exact model tags can vary by what Ollama has available; list models with `ollama list` if needed.

1) Install Ollama: https://ollama.com/download

2) Pull + run:
```bash
ollama pull qwen2.5:7b-instruct
ollama run qwen2.5:7b-instruct
```

3) Optional custom profile (8k context, coding + tool-calling JSON convention): create a `Modelfile`:
```text
FROM qwen2.5:7b-instruct

PARAMETER num_ctx 8192
PARAMETER temperature 0.2
PARAMETER top_p 0.9

SYSTEM """
You are a coding + ops assistant.

When you need to use a tool, respond with EXACTLY one line of JSON in this format and nothing else:
{"tool":"<name>","args":{...}}

Otherwise, respond normally.
"""
```
Build + run:
```bash
ollama create qwen25-coder-tools -f Modelfile
ollama run qwen25-coder-tools
```

4) Local API test:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen25-coder-tools",
  "prompt": "Say OK_QWEN_LOCAL",
  "stream": false
}'
```

## Keeping ~8GB free (practical guidance)
- Keep **context** at **8192** initially (larger context increases memory usage).
- Don’t run multiple local models simultaneously.
- Close heavy browser tabs when running Claude Code + local model.
- Use Activity Monitor → Memory to confirm headroom.

---

# My ClickUp

**File:** `subfolder/desi-thoughts/run-models-on-macair.md`

**Notes:**
- This note captures our discussion around:
  - what “open-weight” means,
  - why Kimi K2.5 is difficult to run locally on a MacBook Air,
  - which laptop-sized quantized models to use instead,
  - runner comparison (Ollama vs llama.cpp vs LM Studio),
  - and a concrete Ollama + Qwen2.5 7B setup targeting ~8GB free memory.

**Last updated (UTC):** 2026-02-07 18:09

**ClickUp list:** CLAWBOTSYNC → Tasks (listId `901710672039`)
