## pccx (Parallel Compute Core eXecutor) Architecture Specification

### 1. Introduction  


1. 프로젝트의 목적 및 배경 (예: LLM, 특히 Gemma 3N 모델의 엣지 디바이스 추론 가속)  
Agent AI의 역할이 중요해지면서 Local LLM의 중요성 또한 같이 높아지고 있다. Gemma와 같은 Local LLM을 FPGA에서 베어메탈 구조로 돌릴수 있다면 기존 CNN 혹은 1B 수준의 모델을 돌리던 FPGA의  판도를 바꿀 수 있다고 생각하여 아키텍쳐를 설계 해 보았다. 
프로젝트의 아키텍쳐 핵심 특징은 `범용성` 이다. 단순히 GEMMA 3N E4B 모델만을 타깃으로 하는 FPGA가 아닌, GEMMA부터 타 모델까지 추론 가능한 NPU를 설계하는것이 이프로젝트의 핵심이다.

1. 기존 아키텍처의 한계와 pccx가 제시하는 해결책 요약  
기존 v001아키텍쳐는 메모리 이동이 잦아서 AI연산의 핵심인 latency가 증가할 위험이 높았음.
GEMM, GEMV, Complex Vectors(sine, cos, tanh)들은 `Activation` 을 공유하기 떄문에 가운데 L2캐시의 위치를 최적화 하면 데이터의 이동 path을 최소화 할 수 있음.

1. 주요 타겟 하드웨어 (Xilinx Kria KV260) 및 목표 성능 지표  
목표 성능은 gemma3N E4B모델을 1초에 20토큰 생성을 목표로 하고 있음.

### 2. Background & Workload Analysis
1. 타겟 워크로드 특성 분석 (Transformer 구조, Matrix Multiplication 비중 등)
 
2. 양자화 전략 (W4A8 등) 적용 이유 및 하드웨어적 이점
레퍼런스 device인 KV260에 들어있는 DSP는 INTEGER(정수형)연산에 최적화 되어있다. 
3. 메모리 대역폭(Bandwidth) 요구사항 분석

### 3. Top-Level Architecture 
![NPU Architecture](/assets/images/Architecture/v001/architecture_v001.png)

* NPU 전체 블록 다이어그램 소개

* 이기종 코어 설계 사상 (Matrix Core vs. Vector Core/SFU 역할 분담)
* 클럭 도메인 분리 전략 (AXI 250MHz vs. Core 400MHz) 및 버스 파이프라이닝

## 4. Microarchitecture & Instruction Set
* **4.1 Instruction Set Architecture (ISA):** 64-bit 명령어 포맷(Opcode, Operand) 및 Dispatcher 디코딩 흐름
* **4.2 Systolic Array & Processing Element (PE):** PE 내부 연산 구조 및 파이프라인 레지스터 배치
* **4.3 Dataflow Strategy:** 가중치(Weight) 및 액티베이션(Activation) 데이터의 매핑 및 재사용 메커니즘
* **4.4 Special Function Unit (SFU):** 비선형 함수(Softmax, GELU 등) 하드웨어 구현 방식
  
## 5. Memory Hierarchy & Interconnect
* L2 Cache, L1 Cache, Constant Cache의 용량 산정 근거 및 역할
* 외부 메모리 인터페이스 (AXI HP, ACP 포트) 및 비동기 FIFO 설계
* 데이터 기아(Starvation) 방지를 위한 대역폭 매칭 수학적 증명

## 6. Implementation & Evaluation (합성 후 채워 넣을 부분)
* FPGA 리소스 사용량 (LUT, DSP, BRAM/URAM Utilization)
* 동작 주파수 (Fmax) 달성 여부 및 타이밍 클로저 결과
* 전력 소모 (Power Estimation) 및 예상 스루풋(GOPS/TOPS)

## 7. Conclusion
* pccx 아키텍처의 설계 성과 요약 및 향후 발전 방향 (예: 컴파일러 통합 등)

