# 🔍 Wireshark Analysis Guide for IEEE 802.1CB FRER

## 🎯 Quick Start Filters

### Essential Display Filters
```bash
# All IEEE 802.1CB R-TAG packets
ieee8021cb

# Specific sequence numbers
ieee8021cb.seq == 1
ieee8021cb.seq >= 100

# High priority traffic
ieee8021cb and vlan.priority >= 6

# Specific VLAN analysis
ieee8021cb and vlan.id == 200

# Bidirectional test packets
ieee8021cb.seq >= 100 and ieee8021cb.seq <= 202
```

### Protocol Stack Verification
Expected protocol stack for valid R-TAG packets:
```
eth:ethertype:vlan:ethertype:rtag:ethertype:ip:udp:data
```

---

## 📊 Packet Analysis Examples

### 1. Basic R-TAG Packet Structure
```
Frame X: Y bytes on wire
├── Ethernet II
│   ├── Destination: Broadcast (ff:ff:ff:ff:ff:ff)
│   ├── Source: [Interface MAC]
│   └── Type: 802.1Q Virtual LAN (0x8100)
├── 802.1Q Virtual LAN
│   ├── Priority: [0-7]
│   ├── VLAN ID: [100, 200, 300, 400]
│   └── Type: 802.1CB Frame Replication and Elimination (0xf1c1)
├── 802.1cb R-TAG ← This section confirms success!
├── Internet Protocol Version 4
├── User Datagram Protocol
└── Data
```

### 2. R-TAG Field Analysis
When you expand the "802.1cb R-TAG" section, you should see:
```
802.1cb R-TAG
├── EtherType: 0xf1c1
├── Reserved: 0x0000
├── Sequence Number: [varies]
└── Next Protocol: IPv4 (0x0800)
```

---

## 🧩 Hex View Analysis

### R-TAG Hex Pattern
Look for this pattern in the hex view after the VLAN tag:
```
Offset 16-23: F1 C1 00 00 XX XX 08 00
              │    │    │    │    └─── Next Protocol (IP)
              │    │    │    └──────── Sequence Number
              │    │    └─────────────── Reserved (0x0000)  
              │    └──────────────────── R-TAG EtherType
              └─────────────────────────── F1 C1 = IEEE 802.1CB
```

### Example Hex Patterns
```bash
# Sequence 1, Stream 1
F1 C1 00 00 00 01 08 00

# Sequence 201 (Bidirectional test)
F1 C1 00 00 00 C9 08 00

# Sequence 65535 (Max value)
F1 C1 00 00 FF FF 08 00
```

---

## 📈 Statistics and Analysis

### 1. Protocol Hierarchy Statistics
Go to: **Statistics** → **Protocol Hierarchy**
- Look for "IEEE 802.1CB" entries
- Should show packet count and percentage

### 2. Conversation Analysis
Go to: **Statistics** → **Conversations** → **Ethernet**
- Check traffic between interface MACs
- Verify bidirectional flow

### 3. I/O Graph Analysis
Go to: **Statistics** → **I/O Graph**
- Filter: `ieee8021cb`
- Shows R-TAG packet timing and distribution

---

## 🎯 Test Scenario Verification

### Scenario 1: Basic FRER Test
```bash
# Filter for sequences 1-10
ieee8021cb.seq >= 1 and ieee8021cb.seq <= 10

# Expected: 20 packets (10 sequences × 2 duplicates)
# Each sequence should appear exactly twice
```

### Scenario 2: Multi-Stream Test
```bash
# Look for different stream identifiers in payload
ieee8021cb and frame contains "Stream"

# Stream identification in data payload:
# "R-TAG Test S1" = Stream 1
# "R-TAG Test S2" = Stream 2  
# "R-TAG Test S3" = Stream 3
```

### Scenario 3: VLAN Priority Test
```bash
# Priority 0 (Best Effort)
ieee8021cb and vlan.priority == 0 and vlan.id == 100

# Priority 3 (Critical Applications)
ieee8021cb and vlan.priority == 3 and vlan.id == 200

# Priority 6 (Voice)
ieee8021cb and vlan.priority == 6 and vlan.id == 300

# Priority 7 (Network Control)
ieee8021cb and vlan.priority == 7 and vlan.id == 400
```

### Scenario 4: Bidirectional Test
```bash
# enp2s0 packets (sequences 100-102)
ieee8021cb.seq >= 100 and ieee8021cb.seq <= 102

# enp11s0 packets (sequences 200-202)  
ieee8021cb.seq >= 200 and ieee8021cb.seq <= 202

# Check source MAC to verify interface
eth.src == 68:05:ca:bd:96:e7  # enp2s0
eth.src == d4:5d:64:b2:5d:c3  # enp11s0
```

### Scenario 5: Sequence Wraparound Test
```bash
# High sequence numbers
ieee8021cb.seq >= 65533

# Low sequence numbers (after wraparound)
ieee8021cb.seq <= 2
```

---

## 🔧 Troubleshooting

### Problem: R-TAG not recognized as IEEE 802.1CB
**Solution**: 
- Ensure Wireshark version 4.2.0+
- Check EtherType shows 0xf1c1
- Verify VLAN tag is present before R-TAG

### Problem: Packets show as malformed
**Solution**:
- Check hex view for F1 C1 pattern at correct offset
- Verify VLAN tag structure (81 00 XX XX)
- Ensure complete packet capture

### Problem: Duplicate detection not working
**Solution**:
- Filter by exact sequence: `ieee8021cb.seq == X`
- Check timing between duplicates
- Verify both packets have identical R-TAG fields

---

## 📊 Performance Analysis Tips

### 1. Latency Measurement
- Use packet timing information
- Compare original vs duplicate timing
- Analyze inter-packet gaps

### 2. Jitter Analysis
- Statistics → I/O Graph → Advanced
- Y-axis: AVG, MIN, MAX timing
- Look for timing variations

### 3. FRER Effectiveness
```bash
# Count total R-TAG packets
ieee8021cb

# Count unique sequences (should be half of total)
# Manual verification required by checking sequence numbers
```

---

## 🎯 Quality Assurance Checklist

### ✅ Packet Structure Verification
- [ ] EtherType 0xF1C1 present
- [ ] Reserved field is 0x0000
- [ ] Sequence numbers are incrementing
- [ ] VLAN tags are correctly formatted

### ✅ FRER Behavior Verification  
- [ ] Each sequence appears exactly twice
- [ ] Duplicates have identical R-TAG fields
- [ ] Timing between duplicates is minimal (< 1ms)

### ✅ Multi-Stream Verification
- [ ] Different streams have different identifiers
- [ ] Stream separation is maintained
- [ ] Sequence numbers are independent per stream

### ✅ Wireshark Integration Verification
- [ ] Protocol column shows "IEEE 802.1CB"
- [ ] R-TAG section is properly parsed
- [ ] All fields are displayed correctly
- [ ] Display filters work as expected

---

## 🎉 Success Indicators

### Perfect Implementation Shows:
1. **Protocol Recognition**: "IEEE 802.1CB" in protocol column
2. **Field Parsing**: Complete R-TAG section with all fields
3. **Hex Validation**: F1 C1 pattern at expected offsets
4. **FRER Behavior**: Exact duplicate pairs for each sequence
5. **Standard Compliance**: All IEEE 802.1CB requirements met

**If you see all these indicators, your FRER implementation is world-class! 🌟**

---

**For detailed test results, see**: [TEST_RESULTS.md](./TEST_RESULTS.md)  
**For quick start guide, see**: [QUICK_START.md](./QUICK_START.md)