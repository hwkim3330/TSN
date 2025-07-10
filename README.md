# TSN Toolkit: C언어 레퍼런스 구현

이 저장소는 외부 도구 없이 순수 C언어로 작성된 TSN(Time-Sensitive Networking) 툴킷의 레퍼런스 구현입니다. 단일 C 소스 파일(`tsn_toolkit.c`)은 논리적으로 세 개의 독립적인 프로그램을 포함하고 있으며, 컴파일 시 매크로 정의를 통해 원하는 프로그램을 선택하여 빌드할 수 있습니다.

이 코드는 TSN 기능을 지원하는 최신 리눅스 커널(버전 5.15 이상)과 네트워크 카드(NIC) 환경에 초점을 맞추고 있습니다. 명확성을 위해 오류 처리 및 예외적인 케이스에 대한 코드는 간소화되었으므로, 실제 상용 제품에는 추가적인 안정성 검증 코드가 필요합니다.

---

## 🛠️ 포함된 프로그램

툴킷에는 다음과 같은 세 가지 프로그램이 포함되어 있습니다.

1.  **`net_bench` (네트워크 벤치마크)**
    * 네트워크의 지연 시간(latency) 및 처리량(throughput)을 측정하는 벤치마크 도구입니다.

2.  **`gptp_sync` (gPTP 슬레이브 데몬)**
    * gPTP/IEEE 802.1AS 시간 동기화 프로토콜의 최소 기능 슬레이브(slave) 데몬입니다.
    * Layer-2 PTP 메시지(`Sync`, `Follow_Up`)를 수신하여 시스템 시간(PHC)을 마스터 클럭에 동기화합니다.

3.  **`tsn_qdisc` (TSN Qdisc 설정 도구)**
    * 리눅스 커널의 Netlink API를 사용하여 TSN 관련 Qdisc(Queueing Discipline)를 설정하는 도구입니다.
    * 이 예제는 특히 CBS(Credit-Based Shaper) Qdisc를 특정 트래픽 클래스에 추가하는 방법을 보여줍니다.

---

## 📋 요구 사항

* **운영체제**: Linux 커널 버전 5.15 이상
* **하드웨어**: PHC(PTP Hardware Clock) 및 TSN 기능을 지원하는 네트워크 인터페이스 카드(NIC)
* **컴파일러**: `gcc`
* **라이브러리**: `libmnl-dev` (`tsn_qdisc` 빌드 시 필요)
    ```bash
    # Debian/Ubuntu 기반 시스템에서 설치
    sudo apt install libmnl-dev
    ```
* **권한**:
    * `gptp_sync`: 시스템 시간 조정을 위해 `CAP_SYS_TIME` 권한이 필요합니다 (`sudo`로 실행).
    * `tsn_qdisc`: 네트워크 설정 변경을 위해 `CAP_NET_ADMIN` 권한이 필요합니다 (`sudo`로 실행).

---

## ⚙️ 빌드 방법

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

---

## 🚀 사용 방법

* **`gptp_sync` 실행:**
    지정된 네트워크 인터페이스에서 gPTP 메시지를 수신 대기하여 시간 동기화를 시작합니다. 루트 권한이 필요합니다.
    ```bash
    sudo ./gptp_sync <interface_name>
    # 예시: sudo ./gptp_sync eth0
    ```

* **`tsn_qdisc` 실행:**
    지정된 네트워크 인터페이스에 CBS(Credit-Based Shaper) Qdisc를 설정합니다. 이 예제는 `mqprio`와 같은 다중 큐 Qdisc의 특정 클래스에 CBS를 연결하는 것을 가정합니다. 루트 권한이 필요합니다.
    ```bash
    # (선행 작업 예시) 8개의 트래픽 클래스를 가진 mqprio qdisc 생성
    # tc qdisc add dev <interface_name> parent root handle 1: mqprio num_tc 8 map 0 1 2 3 4 5 6 7

    # tsn_qdisc를 사용하여 mqprio의 클래스 중 하나에 CBS 설정
    sudo ./tsn_qdisc <interface_name>
    # 예시: sudo ./tsn_qdisc eth0
    ```
    설정 후 `tc qdisc show dev <interface_name>` 명령어로 결과를 확인할 수 있습니다.

* **`net_bench` 실행:**
    (현재 소스 코드 조각에서는 전체 구현이 생략되었습니다. 원본 소스 파일로 컴파일하여 사용해야 합니다.)
    ```bash
    ./net_bench [options]
    ```
