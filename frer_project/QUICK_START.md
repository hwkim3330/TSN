# 🚀 Quick Start Guide

## Prerequisites

- Ubuntu 22.04+ with Intel i210/i225 NICs
- Wireshark 4.2.0+ (for official 802.1CB support)
- Python 3.8+
- Root privileges

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/hwkim3330/tsn.git
cd tsn/frer_project
```

### 2. Install Dependencies
```bash
# System packages
sudo apt update
sudo apt install python3-dev libpcap-dev tcpdump iproute2 wireshark

# Python packages
python3 -m venv frer_env
source frer_env/bin/activate
pip install -r requirements.txt
```

### 3. Setup Network Interfaces
```bash
sudo ./setup_environment.sh
```

## Running Tests

### Basic FRER Test
```bash
# Terminal 1: Start Wireshark capture on enp2s0
wireshark -i enp2s0 -k -f "vlan 100"

# Terminal 2: Send FRER test packets
sudo python3 frer_wireshark_official.py
```

### Real-time Analysis
```bash
# Terminal 1: Send test packets
sudo python3 frer_analysis_tool.py send

# Terminal 2: Monitor and analyze
sudo python3 frer_analysis_tool.py
```

## Expected Results

### In Wireshark:
- Protocol column shows: **"IEEE 802.1CB"**
- R-TAG fields correctly parsed
- Each sequence number appears exactly **2 times**

### Filters to Use:
```bash
ieee8021cb                 # All R-TAG packets
ieee8021cb.seq == 1       # Sequence 1 only
ieee8021cb.etype == 0xf1c1 # R-TAG EtherType
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Operation not permitted" | Run with `sudo` |
| "No such device" | Check interface names with `ip link` |
| Wireshark doesn't show R-TAG | Ensure Wireshark 4.2.0+ |
| Packets not captured | Check VLAN configuration |

## Verification

✅ **Success indicators:**
- Wireshark shows "802.1CB Frame Replication and Elimination for Reliability"
- R-TAG fields: EtherType (0xf1c1), Reserved (0x0000), Sequence (0x0001-0x0005)
- Duplicate elimination rate: 50% (5 originals + 5 duplicates = 10 total)

---
**Need help?** Check the main README.md or create an issue on GitHub.