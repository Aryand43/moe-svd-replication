# MoE SVD Compression: Reproduction & Extension

**Reproduction and extension of SVD-based Mixture-of-Experts (MoE) compression,  
following recent research and adapting for further HPC experimentation.**

**Maintainer:** Aryan Dutt
---

This repo closely reproduces the methodology and code flow of recent MoE SVD compression frameworks (see references).  
- All scripts have been thoroughly annotated and documented for clarity.
- Some minor refactoring and test functions have been added for debugging, reproducibility, and future GPU deployment.
- Code is tested on both CPU and GPU, and ready for extension into CUR decomposition as discussed.

**Key components:**  
- Gating (softmax, top-K expert selection)
- SVD-based compression for expert weights
- Sensitivity/outlier analysis
- [Planned] CUR-based variant for improved interpretability

> *This repo will be further extended for joint experiments with Dr. Rabab Alomairy. All code is open, reproducible, and aligned with MoE literature best practices.*
# TODO: Extend SVD compression to CUR decomposition for enhanced interpretability.
# TODO: Port to full-scale LLM weights (DeepSeek/Mixtral) on GPU cluster.
# TODO: Benchmark sensitivity, routing frequency, and memory savings.
