# Dynamo stump-authoring dataset

Fine-tuning data distilled from this campaign's **measured** design→outcome record
against Opus-4.8 + Terminus-2: every accepted stump, every solved design, every
rubric rejection, every design-table kill — plus the distilled decision principles
(placement ladder, seed gate, poison geometry, anti-checklist).

- `build_dataset.py` — the curated source of truth. Records and principles live here
  as data; the script expands them into chat-format JSONL.
- `train.jsonl` / `valid.jsonl` / `all.jsonl` — generated. Each line:
  `{"messages": [{role: system|user|assistant, content: ...}]}`.

## The standing rule (this is the moat)

**After every task, pass@ run, review, or design-table kill: append a new
`DesignRecord` (and any new `Principle`) to `build_dataset.py` and re-run it.**
The dataset's value is real labels measured against the frontier model — those
compound; clever synthetic examples don't.

## What to expect (honest)

~60 curated examples LoRA-tuned into a 7–8B model teaches the *decision rules*:
it will reliably kill dead designs (stated-rule pattern A, recoverable secrets,
tool-oracle seeds), run the seed gate, and recite/apply the poison geometry — a
useful always-on design critic. It will not out-invent Opus-4.8 from data this
size. Stumping comes from the measured record + the procedure; the local model is
a way to bottle the procedure.

## Fine-tune on a Mac (MLX-LM), then serve with Ollama

```bash
pip install mlx-lm

# LoRA fine-tune (chat-format JSONL is supported natively; this dir already has
# train.jsonl and valid.jsonl)
mlx_lm.lora \
  --model Qwen/Qwen2.5-7B-Instruct \
  --train --data ~/Work/dynamo-log-report-task/training-data \
  --iters 400 --batch-size 2 --num-layers 16

# sanity-check the adapter
mlx_lm.generate --model Qwen/Qwen2.5-7B-Instruct --adapter-path adapters \
  --prompt "Review this task design and predict the pass@2 outcome: a custom \
binary format where all rules are stated in the spec and a latent rule never \
fires on the samples."

# fuse the adapter into the base weights
mlx_lm.fuse --model Qwen/Qwen2.5-7B-Instruct --adapter-path adapters \
  --save-path fused-model

# convert to GGUF (llama.cpp) and register with Ollama
python llama.cpp/convert_hf_to_gguf.py fused-model --outfile dynamo-critic.gguf
cat > Modelfile << 'EOF'
FROM ./dynamo-critic.gguf
PARAMETER temperature 0.3
SYSTEM "You are a Project Dynamo task-design expert..."  # use SYSTEM from build_dataset.py
EOF
ollama create dynamo-critic -f Modelfile
ollama run dynamo-critic
```

Notes:
- On CUDA hardware, Unsloth or LLaMA-Factory consume the same JSONL (OpenAI chat
  format) — pick either; export GGUF the same way.
- Small dataset → keep LoRA rank/layers modest and iterations low (overfitting the
  exact wording is fine here; these are rules, not general knowledge).
- Re-run the whole loop after appending new records; the dataset regenerates
  deterministically (fixed shuffle seed).
- Evaluation idea: hold out the newest task's records and check the critic
  predicts its outcome + mechanism before you push — i.e., use the model as a
  pre-push gate and score it against reality over time.
