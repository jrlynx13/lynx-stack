# Adreno OpenCL LLM notes

Running quantized LLMs on the Adreno 830 GPU (Snapdragon 8 Elite, Samsung
S25 Ultra) via [llama.cpp](https://github.com/ggml-org/llama.cpp)'s OpenCL
backend. Tested up to ~4B parameter models at usable interactive speed.

Why OpenCL not Vulkan: see [q4_0-pure-vs-q4_k_m.md](q4_0-pure-vs-q4_k_m.md)
for the key gotcha. Vulkan crashes outright for ≥ 4B models on Adreno 830;
OpenCL is the only working backend at that scale.

## Pages

- [Q4_K_M has no Adreno OpenCL kernel — use Q4_0+pure instead](q4_0-pure-vs-q4_k_m.md)
- (more to come — Vulkan-fails-4B+, build flags, model survey)
