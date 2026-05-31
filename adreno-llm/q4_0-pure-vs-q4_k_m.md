# Q4_K_M has no Adreno OpenCL kernel — quietly costs you ~50 % throughput

If you grabbed a "recommended" `*-Q4_K_M.gguf` off Hugging Face and you're
running it on Adreno via `llama.cpp`'s OpenCL backend, you are almost
certainly leaving a huge throughput improvement on the table.

## The trap

`llama.cpp`'s OpenCL backend ships kernels for a limited subset of
quantization formats. As of mid-2026 it **does not have a kernel for the
K-quants** (Q3_K, Q4_K_M, Q4_K_S, Q5_K_M, Q5_K_S, Q6_K). When the OpenCL
backend hits a tensor in an unsupported format, it falls back to **CPU**
for that layer. Most modern models ship dequant code that's mixed across
the model — so you end up running ~half the work on the CPU and half on
the GPU, paying the dispatch cost both ways.

Net effect on the S25 Ultra (12 GB):

| Format         | Tokens/sec (Qwen3-4B-Instruct, 4 GB context) |
| -------------- | -------------------------------------------- |
| `Q4_K_M`       | 11.5 (CPU fallback active)                   |
| `Q4_0` + pure  | 18.4                                         |

About a **60 % throughput uplift** for the same model weights and same
prompt, just from picking a quantization the GPU backend can actually run.

You can confirm the CPU fallback is happening with
`llama-bench` — the `tg128` number for `Q4_K_M` will be close to the
CPU-only number for the same model, while `pp512` (prompt processing)
will be GPU-fast. That asymmetry is the signature.

## What "pure" means

The `+pure` suffix is GGUF tooling shorthand for "every tensor was quantized
to the requested format, no mixed K-quants for the harder-to-quantize
tensors." Default `Q4_0` quantization actually leaves the embedding +
output tensors at higher precision (which is fine), but historically also
mixed in K-quants for "attention" tensors — which trips the OpenCL
fallback again.

You want a model file that is honest-to-god `Q4_0` end to end with no
K-quant mixed in. The `Q4_0-pure` convention is the cleanest signal.

## How to get a pure Q4_0 GGUF

Three options.

**A. Pre-built from Unsloth / community.** Search Hugging Face for
`<model>-GGUF` with `q4_0-pure` or `Q4_0_PURE` in the filename. Quality
varies; check the model card for the conversion command used.

**B. Convert yourself with llama.cpp tools.** From a `f16.gguf` base:

```bash
./llama-quantize <model>.f16.gguf <model>.q4_0-pure.gguf q4_0 \
    --pure
```

`--pure` is the flag that disables the K-quant mixing for the
embed-output and attention tensors. Without it you get the default
"Q4_0 + K-quant sprinkles" that triggers the fallback.

**C. The `--token-embedding-type` / `--output-tensor-type` overrides.**
If you want the embed + output at f16 (less degradation) but everything
else at strict Q4_0:

```bash
./llama-quantize <model>.f16.gguf <model>.q4_0-mixed.gguf q4_0 \
    --pure \
    --token-embedding-type f16 \
    --output-tensor-type f16
```

The embed/output run on CPU anyway, so f16 there doesn't slow anything
down on the GPU side.

## Reference setup

llama.cpp OpenCL build:

```bash
cmake -B build-opencl -DGGML_OPENCL=ON
cmake --build build-opencl -j
```

Termux package: `pkg install opencl-clhpp opencl-headers ocl-icd`.

Adreno OpenCL ICD lives in the Android system libs under
`/system/vendor/lib64/libOpenCL.so` and is exposed to Termux via the
shared `/system` mount — no manual ICD setup needed.

Run with `--gpu-layers <N>` matching your VRAM budget. For Qwen3-4B at
Q4_0-pure on the S25 Ultra, all layers fit; use `--gpu-layers 99`.

## Vulkan note

Don't try Vulkan as a workaround. The current `GGML_VULKAN` backend
crashes outright (segfault or shader-compile fail) for models ≥ 4B on
Adreno 830 — verified May 2026. OpenCL is the only working GPU path at
that model size right now. Sub-3B models work on Vulkan; 4B+ does not.

## Sources

- Verified live on Samsung S25 Ultra, llama.cpp build b8734 with the
  OpenCL backend, Qwen3-4B-Instruct in both quant variants, ~5,000-token
  prompts.
- Backend kernel coverage cross-referenced against
  `ggml/src/ggml-opencl/kernels/` in the llama.cpp tree (which formats
  have a `.cl` file ≈ which formats run on the GPU).
