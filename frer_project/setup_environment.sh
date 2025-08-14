#!/bin/bash

# Setup FRER Test Environment
# Configure direct link between i210 (enp2s0) and i225 (enp11s0)

echo "=== Setting up FRER Test Environment ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Interfaces
SENDER_IF="enp2s0"    # i210
RECEIVER_IF="enp11s0" # i225

echo "Configuring interfaces for FRER testing..."

# Bring interfaces up
ip link set $SENDER_IF up
ip link set $RECEIVER_IF up

# Create VLAN 100 for FRER traffic
ip link add link $SENDER_IF name ${SENDER_IF}.100 type vlan id 100
ip link add link $RECEIVER_IF name ${RECEIVER_IF}.100 type vlan id 100

# Set VLAN priority mapping for FRER (high priority)
ip link set dev ${SENDER_IF}.100 type vlan egress 0:3 1:3 2:3 3:3 4:3 5:3 6:3 7:3
ip link set dev ${RECEIVER_IF}.100 type vlan egress 0:3 1:3 2:3 3:3 4:3 5:3 6:3 7:3

# Bring VLAN interfaces up
ip link set ${SENDER_IF}.100 up
ip link set ${RECEIVER_IF}.100 up

# Assign IP addresses for testing
ip addr add 192.168.100.1/24 dev ${SENDER_IF}.100
ip addr add 192.168.100.2/24 dev ${RECEIVER_IF}.100

# Configure qdisc for low latency
tc qdisc del dev $SENDER_IF root 2>/dev/null || true
tc qdisc del dev $RECEIVER_IF root 2>/dev/null || true

# Use simple pfifo for minimal latency
tc qdisc add dev $SENDER_IF root handle 1: pfifo limit 10
tc qdisc add dev $RECEIVER_IF root handle 1: pfifo limit 10

echo "Network configuration completed:"
echo "  Sender: ${SENDER_IF} (${SENDER_IF}.100 - 192.168.100.1)"
echo "  Receiver: ${RECEIVER_IF} (${RECEIVER_IF}.100 - 192.168.100.2)"

# Test connectivity
echo ""
echo "Testing connectivity..."
ping -c 3 -W 1 192.168.100.2 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Connectivity test passed"
else
    echo "⚠ Connectivity test failed (normal if interfaces not physically connected)"
fi

# Enable promiscuous mode for packet capture
echo ""
echo "Enabling promiscuous mode for packet capture..."
ip link set $SENDER_IF promisc on
ip link set $RECEIVER_IF promisc on
echo "✓ Promiscuous mode enabled"

# Setup Wireshark dissector
WIRESHARK_PLUGINS_DIR="$HOME/.local/lib/wireshark/plugins"
mkdir -p "$WIRESHARK_PLUGINS_DIR"

if [ -f "/home/kim/rtag_dissector.lua" ]; then
    cp /home/kim/rtag_dissector.lua "$WIRESHARK_PLUGINS_DIR/"
    echo "✓ R-TAG Wireshark dissector installed to $WIRESHARK_PLUGINS_DIR"
    echo "  Restart Wireshark to load the dissector"
else
    echo "⚠ R-TAG dissector not found"
fi

echo ""
echo "=== FRER Test Environment Ready ==="
echo ""
echo "🔧 CONFIGURATION:"
echo "  • Sender Interface: $SENDER_IF (i210)"
echo "  • Receiver Interface: $RECEIVER_IF (i225)" 
echo "  • VLAN ID: 100 (Priority 3)"
echo "  • IP Range: 192.168.100.0/24"
echo ""
echo "📊 WIRESHARK SETUP:"
echo "  • Capture Interface: $RECEIVER_IF"
echo "  • Display Filter: vlan.id == 100"
echo "  • R-TAG Filter: rtag (after loading dissector)"
echo ""
echo "🚀 TO START FRER TEST:"
echo "  sudo python3 /home/kim/frer_test.py"
echo ""
echo "🔍 MANUAL ANALYSIS:"
echo "  • R-TAG Location: 6 bytes after VLAN header"
echo "  • Hex Pattern: frame[18:6] for R-TAG bytes"
echo "  • Stream Filter: frame[22:2] == 00:01 (stream 1)"
echo ""
echo "Ready for FRER testing!"