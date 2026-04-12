# uCA: micro Compute Architecture

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Scalable_NPU-purple)
![Target](https://img.shields.io/badge/Target-Edge_AI-orange)
![Precision](https://img.shields.io/badge/Precision-W4A8_Promotion-green)

> **Notice: Active Development in Progress** > uCA is a scalable and modular Neural Processing Unit (NPU) architecture designed to accelerate Transformer-based Large Language Models (LLMs) on resource-constrained edge devices. 

---

## 1. Architecture Overview

uCA is a device-agnostic hardware-software co-design framework. It focuses on breaking the memory bandwidth and compute bottlenecks of edge hardware by scaling the core architecture to the specific physical resource budget of the target device.

### 1.1 Ecosystem Structure

The project is strictly separated into three layers to ensure maximum portability and scalability:

* **`/architecture` (The Logic Layer)** * Contains the core RTL (Register Transfer Level) logic and generation parameters.  
    * Defines the logical pipeline, instruction scheduling, and the **Custom 64-bit ISA**.  
    * This layer is independent of any specific hardware vendor or interface protocol.

* **`/device` (The Implementation Layer)** * Mappings of the uCA architecture onto specific hardware targets.  
    * Adjusts the number of compute cores, systolic array dimensions, and memory port widths based on the available resource budget (e.g., DSP count, local memory size).  
    * Handles the physical constraints of different hardware platforms.

* **`/driver` (The Software Layer)** * Provides a C/C++ Hardware Abstraction Layer (HAL) and high-level API.  
    * Manages instruction dispatching and memory mapping, acting as the bridge between high-level AI models and the uCA hardware.

---

## 2. Key Technical Features

### 2.1 Decoupled Dataflow & Custom ISA  
The architecture utilizes a **Custom 64-bit ISA** optimized for matrix and vector operations. It employs a **Decoupled Dataflow** pipeline, separating instruction decoding from execution to eliminate pipeline stalls and maximize throughput.

### 2.2 W4A8 Dynamic Precision Promotion  
To maintain both efficiency and accuracy:  
* **Compute:** Parallel 2D Systolic Array executes high-density **INT4 (Weight) × INT8 (Activation)** operations.  
* **Promotion:** During non-linear operations (Softmax, RMSNorm, GeLU), the architecture automatically promotes precision to **BF16 / FP32** within the Complex Vector Operation (CVO) core to preserve numerical integrity.

### 2.3 Tiered Memory Hierarchy  
* **Matrix Core:** Dedicated to GEMM operations with a scalable array size.  
* **Vector Core:** Handles GEMV and element-wise operations.  
* **Shared Interconnect:** A flexible data bus system that allows simultaneous access between cores and local caches without arbitration overhead.

---

## 3. Documentation

Detailed technical specifications are located in the `/docs` directory:  
1. `uCA_ISA_Spec.md`: Specification of the 64-bit Custom Instruction Set.  
2. `Architecture_Scaling.md`: Guidelines for mapping logic to physical resources.  
3. `API_Reference.md`: Documentation for the uCA Driver and SDK.

---

## 4. License

This project is licensed under the **Apache License 2.0**. It provides freedom of use and modification while protecting the architecture against patent-related risks, ensuring a safe ecosystem for open-source hardware development.