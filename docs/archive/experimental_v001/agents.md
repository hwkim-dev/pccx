# 🤖 NPU Runtime Agents (Task Dispatchers)

이 문서는 설계된 v001 아키텍처 파이프라인 내의 자율 제어 및 디스패치 루틴을 설명합니다. uXC NPU는 성능 극대화 및 병목 최소화를 위해 단순한 순차 처리가 아니라, **각 실행 유닛이 '미니 에이전트(Agent)' 로서 독립적으로 동작하는 분산 및 디커플링(Decoupling) 파이프라인 패턴**을 갖고 있습니다.

이러한 패턴을 호스트부터 NPU 말단 코어까지의 계층적 에이전트 트리로 이해할 수 있습니다.

---

## 1. 👑 Host Execution Agent (llm-lite)

Python 또는 C++ 단의 호스트(리눅스 또는 베어메탈 프로세서)에서 LLM의 Forward 연산을 주관합니다. 가중치 인출, KV 캐싱, Attention 수식 구조를 그립니다.

- **역할:** NPU의 VLIW(64-bit) Assembly 커맨드를 렌더링하고 `uCA_API`(`uca_gemv`, `uca_cvo` 등)를 통해 큐에 쏟아냅니다.
- **특징:** 명령 수행이 시작되었는지 끝났는지 기다리지 않고 완전히 비동기적으로 지시만 내린 뒤, 결과값이 필요한 다음 어텐션 Phase 직전 부분(`uca_sync`)에서만 대기합니다.

---

## 2. 🚦 Global Front-End Agent (`ctrl_npu_decoder`)

호스트로부터 HPM (AXI-Lite) 라인을 통해 수신된 64-bit 명령어를 분석(Decode)하는 문지기 에이전트입니다.

- **비동기 스케줄링:** 자신이 모든 엔진의 스케줄링 흐름과 자원을 일일이 관리하지 않습니다. 그저 Opcode가 GEMM인지 CVO인지를 보고, **각 하부 엔진이 가진 고유 Instruction FIFO(큐)에 목적지 우편물을 꽂기만 하고 자신의 역할을 끝냅니다.**
- **Pipeline Stall Free:** 특정 코어 유닛이 병목 상태에 있더라도 Global Decoder 단은 블록킹(Stall)되지 않고 다음 명령어 배포 작업을 이어나갈 수 있습니다.

---

## 3. 🎯 Local Dispatcher Agents (Micro-Cores)

파이프라인의 말단 연산 노드인 실행 코어들(`Matrix Core`, `Vector Core`, `CVO Core`)은 각자의 Queue에서 스스로 명령을 꺼내는(Fetch) Local Agent를 소유하고 있습니다.

### A. GEMM / GEMV Dispatcher
Matrix Core 및 Vector Core에 위치합니다. 
로컬 Dispatcher는 자신의 FIFO에서 명령어를 확인한 뒤 다음과 같은 상태 점검을 시작합니다:
1. "입력 활성 데이터(Feature Map)가 L1 버퍼에 준비되었는가?"
2. "가중치 데이터 통신 채널(HP AXI)이 현재 사용 가능한 상태인가?"
3. 조건을 모두 만족하면, 비로소 **스스로 Firing하여 하드웨어 파이프 연산을 트리거**합니다.

### B. CVO (Complex Vector Operations) Dispatcher
수학 함수 엔진(CORDIC/SFU)은 행렬 엔진과 독립적입니다. L2 캐시 라인 상주 공간을 점유하긴 하나 행렬 엔진과의 자원 타협이나 간섭을 거치지 않습니다.
마찬가지로 2048-deep의 대기열 큐와 함께, 앞 단의 Activation Output과 `e_max` 정보가 넘어오는 순간 스스로 `exp`, `sqrt`, `scale` 연산의 Phase를 가동합니다.

---

> [!TIP]
> **왜 이런 Agent 구조를 채택했나요?** <br/>
> 일반적인 순차 하드웨어는 특정 연산에서 Stall 이 났을 때 시스템 전체 사이클이 멈춥니다(Bubble Pipeline). 그러나 디커플되는 모델에서는 호스트가 GPU에 DMA 버퍼링하듯 마음껏 연산을 쏘아 올리고, 하위 수직 모듈들(미니 에이전트)이 각자 조건이 성립될 때만 알아서 일하며 데이터를 Pass 함으로써 1.2M DSP 효율을 최대한 뽑아냅니다.
