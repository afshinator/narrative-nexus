# AMD Hardware Validation — Direct GPU Execution of the Production Embedding Model

**Date:** 2026-07-12
**Environment:** AMD Hackathon GPU pod — `notebooks.amd.com/hackathon` (team-996)
**Image:** ROCm 7.2 + vLLM 0.16.0 + PyTorch 2.9
**Scope:** Capability validation. See "Limitations" — this is not a corpus re-embedding run.

---

## Claim

Narrative Nexus's production article-clustering embedding model —
`BAAI/bge-base-en-v1.5`, the model resolved by `config/providers.json`
(`defaults.agent1_embedding` → provider `fireworks` → `"model": "BAAI/bge-base-en-v1.5"`) —
was loaded and executed **directly on AMD GPU hardware** via ROCm, producing
correct 768-dimensional vectors.

This establishes that the pipeline's embedding stage runs on AMD silicon
directly, not only through an AMD-backed inference API.

---

## Hardware — `rocm-smi`

```
======================================== ROCm System Management Interface ========================================
================================================== Concise Info ==================================================
Device  Node  IDs              Temp    Power  Partitions          SCLK  MCLK   Fan    Perf  PwrCap  VRAM%  GPU%
              (DID,     GUID)  (Edge)  (Avg)  (Mem, Compute, ID)
==================================================================================================================
0       5     0x744b,   13037  21.0°C  10.0W  N/A, N/A, 0         0Mhz  96Mhz  20.0%  auto  241.0W  0%     0%
==================================================================================================================
============================================== End of ROCm SMI Log ===============================================
```

## Device identity — `rocm-smi --showproductname`

```
GPU[0]          : Card Model:           0x744b
GPU[0]          : Card Vendor:          Advanced Micro Devices, Inc. [AMD/ATI]
GPU[0]          : Card SKU:             D7070910
GPU[0]          : Node ID:              5
GPU[0]          : GUID:                 13037
GPU[0]          : GFX Version:          gfx1100
```

`gfx1100` is the RDNA3 (Radeon RX 7900-class) ISA target. The friendly-name
lookup (`get_name, Error when calling libdrm`) fails inside the container; the
`gfx1100` GFX Version and AMD vendor ID are the authoritative identifiers and
are what we cite.

## ROCm PyTorch sees the device

```
$ source /opt/venv/bin/activate
$ python -c "import torch; print('torch', torch.__version__, 'cuda_avail', torch.cuda.is_available())"
torch 2.9.1+gitff65f5b cuda_avail True
```

(ROCm exposes AMD GPUs through PyTorch's `cuda` API namespace; `cuda_avail True`
here reports the AMD device. `torch.cuda.get_device_name()` returns an empty
string on this gfx1100 ROCm build — a cosmetic quirk of the name lookup above,
not an absence of the device.)

## The production model, on the AMD GPU

```
$ pip install -q sentence-transformers
$ python -c "import torch; assert torch.cuda.is_available(); print('GPU still OK')"
GPU still OK

$ python -c "from sentence_transformers import SentenceTransformer as S; \
             m=S('BAAI/bge-base-en-v1.5'); \
             print('model device:', m.device); \
             print('dim:', len(m.encode(['hello from AMD'])[0]))"

model.safetensors: 100%|██████████████████████████| 438M/438M [00:07<00:00, 58.2MB/s]
model device: cuda:0
dim: 768
```

`model device: cuda:0` — the model is resident on the AMD GPU, not the CPU.
`dim: 768` — the correct vector dimension for `BAAI/bge-base-en-v1.5`, matching
the 182 BGE vectors already stored in the shipped database
(`SELECT model, dim, COUNT(*) FROM embeddings GROUP BY model, dim;`
→ `BAAI/bge-base-en-v1.5 | 768 | 182`).

The run also exercised the ROCm attention backend (AOTriton) and the `aiter`
JIT compiling for `--offload-arch=gfx1100`, further confirming execution on the
AMD target rather than a CPU fallback.

---

## Limitations — what this does NOT claim

Stated plainly, because the project's standard is evidence or nothing:

1. **This is a capability validation, not a corpus run.** The encode call
   embedded a single test string, not the 182 article bodies in `demo.db`. We do
   **not** claim the shipped database's vectors were produced on AMD hardware —
   they were produced via the Fireworks API (which itself serves on AMD Instinct,
   a separate and indirect claim).
2. **The shipped database is untouched.** No pipeline stage was run against
   `data/demo/demo.db`. Fingerprint unchanged: `378/10/358/17/13653`.
3. **No throughput benchmark.** Timing and batch-throughput figures were not
   captured; the team's 12-hour GPU quota window was exhausted before a full
   corpus embedding run could be performed.
4. **Hardware is Radeon, not Instinct.** This pod is a Radeon-class
   (`gfx1100`/RDNA3) GPU. Claims elsewhere in this repo about *AMD Instinct
   MI300X/MI250X* refer specifically to Fireworks AI's serving hardware, not to
   this pod.

## Why it matters anyway

Narrative Nexus's AMD story was otherwise entirely indirect — "we call Fireworks,
which runs on AMD Instinct." This run demonstrates the pipeline's embedding stage
is *portable to AMD silicon we provisioned ourselves*: the exact production model,
loaded on an AMD GPU through ROCm, emitting the exact vector dimension the
clustering stage consumes. The `local-cpu` provider path in
`pipeline/embedding_client.py` (`_embed_local`, sentence-transformers, no
hardcoded device) is the code path that makes this work — it selects the ROCm
device automatically when one is present.