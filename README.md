# TSN (Time-Sensitive Networking) Repository

🌐 **Complete TSN implementation suite including C toolkit and IEEE 802.1CB FRER test framework**

## 📁 Repository Structure

```
📦 TSN Repository
├── 🔧 tsn_toolkit.c          # C언어 TSN 레퍼런스 구현
└── 📡 frer_project/          # IEEE 802.1CB FRER 테스트 슈트 (NEW!)
    ├── frer_wireshark_official.py
    ├── frer_analysis_tool.py
    ├── rtag_dissector.lua
    └── README.md
```

---

## 🆕 **NEW: IEEE 802.1CB FRER Project**

### 🎯 Overview
Complete software implementation of **IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER)** for Intel TSN-capable NICs.

### ✨ Key Features
- **✅ IEEE 802.1CB Standard Compliant** R-TAG generation
- **✅ Frame Replication** (Sender side) 
- **✅ Duplicate Elimination** (Receiver side)
- **✅ Wireshark Official Support** (Protocol: "IEEE 802.1CB")
- **✅ Real-time Analysis** tools

### 🛠️ Technologies Used
- **Scapy** - Advanced packet crafting and analysis
- **Raw Sockets** - Direct Ethernet frame manipulation
- **Python struct** - Binary R-TAG header construction
- **Wireshark Lua** - Custom protocol dissectors

### 🚀 Quick Start
```bash
cd frer_project/
sudo python3 frer_wireshark_official.py  # Send FRER test packets
```

**➡️ [See complete FRER documentation](./frer_project/README.md)**

---

## 🔧 **TSN Toolkit: C언어 레퍼런스 구현**

이 저장소는 외부 도구 없이 순수 C언어로 작성된 TSN(Time-Sensitive Networking) 툴킷의 레퍼런스 구현입니다. 단일 C 소스 파일(`tsn_toolkit.c`)은 논리적으로 세 개의 독립적인 프로그램을 포함하고 있으며, 컴파일 시 매크로 정의를 통해 원하는 프로그램을 선택하여 빌드할 수 있습니다.

이 코드는 TSN 기능을 지원하는 최신 리눅스 커널(버전 5.15 이상)과 네트워크 카드(NIC) 환경에 초점을 맞추고 있습니다.

### 🛠️ 포함된 프로그램

1.  **`net_bench` (네트워크 벤치마크)**
    * 네트워크의 지연 시간(latency) 및 처리량(throughput)을 측정하는 벤치마크 도구입니다.

2.  **`gptp_sync` (gPTP 슬레이브 데몬)**
    * gPTP/IEEE 802.1AS 시간 동기화 프로토콜의 최소 기능 슬레이브(slave) 데몬입니다.
    * Layer-2 PTP 메시지(`Sync`, `Follow_Up`)를 수신하여 시스템 시간(PHC)을 마스터 클럭에 동기화합니다.

3.  **`tsn_qdisc` (TSN Qdisc 설정 도구)**
    * 리눅스 커널의 Netlink API를 사용하여 TSN 관련 Qdisc(Queueing Discipline)를 설정하는 도구입니다.
    * 이 예제는 특히 CBS(Credit-Based Shaper) Qdisc를 특정 트래픽 클래스에 추가하는 방법을 보여줍니다.

### 📋 요구 사항

* **운영체제**: Linux 커널 버전 5.15 이상
* **하드웨어**: PHC(PTP Hardware Clock) 및 TSN 기능을 지원하는 네트워크 인터페이스 카드(NIC)
* **컴파일러**: `gcc`
* **라이브러리**: `libmnl-dev` (`tsn_qdisc` 빌드 시 필요)
    ```bash
    # Debian/Ubuntu 기반 시스템에서 설치
    sudo apt install libmnl-dev
    ```

### ⚙️ 빌드 방법

각 프로그램은 컴파일러 플래그(`-DAPP_*`)를 사용하여 개별적으로 빌드합니다.

* **net_bench 빌드:**
    ```bash
    gcc -O2 -pthread -o net_bench tsn_toolkit.c -DAPP_NET_BENCH
    ```

* **gptp_sync 빌드:**
    ```bash
    gcc -O2 -o gptp_sync tsn_toolkit.c -DAPP_GPTP_SYNC
    ```

* **tsn_qdisc 빌드:**
    ```bash
    gcc -O2 -lmnl -o tsn_qdisc tsn_toolkit.c -DAPP_TSN_QDISC
    ```

### 🚀 사용 방법

* **`gptp_sync` 실행:**
    ```bash
    sudo ./gptp_sync <interface_name>
    # 예시: sudo ./gptp_sync eth0
    ```

* **`tsn_qdisc` 실행:**
    ```bash
    sudo ./tsn_qdisc <interface_name>
    # 예시: sudo ./tsn_qdisc eth0
    ```

* **`net_bench` 실행:**
    ```bash
    ./net_bench [options]
    ```

---

## 🔍 **Comparison: C Toolkit vs Python FRER**

| Feature | C Toolkit | Python FRER |
|---------|-----------|-------------|
| **Language** | Pure C | Python + Scapy |
| **Target** | Basic TSN functions | IEEE 802.1CB FRER |
| **Dependencies** | libmnl only | Scapy, matplotlib |
| **Performance** | ⚡ High performance | 📊 Rich analysis |
| **Use Case** | Production systems | Testing & validation |

---

## 🎯 **Hardware Tested**

- **Intel i210** (TSN-capable Gigabit Ethernet)
- **Intel i225** (TSN-capable 2.5G Ethernet)  
- **Ubuntu 22.04** with Linux kernel 5.15+
- **Wireshark 4.2.2** with official 802.1CB support

## 📈 **Project Status**

| Component | Status | Description |
|-----------|--------|-------------|
| **C Toolkit** | ✅ Stable | Production-ready TSN basics |
| **FRER Implementation** | ✅ Complete | IEEE 802.1CB compliant |
| **Wireshark Integration** | ✅ Working | Official dissector support |
| **Real-time Analysis** | ✅ Available | Performance monitoring |

---

## 🤝 **Contributing**

Contributions welcome! Please check:
- C toolkit for low-level TSN implementations
- Python FRER for protocol testing and validation
- Documentation improvements
- Hardware compatibility testing

## 📄 **License**

MIT License - See individual project files for details

---

**Repository**: https://github.com/hwkim3330/TSN  
**Author**: hwkim3330  
**Last Updated**: August 2025