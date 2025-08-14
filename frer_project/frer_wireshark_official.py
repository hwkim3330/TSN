#!/usr/bin/env python3
"""
FRER Test with Wireshark Official R-TAG Support
Using proper packet structure for official dissector recognition
"""

import sys
import os
import time
import struct
import socket

sys.path.insert(0, '/home/kim/tsn_venv/lib/python3.12/site-packages')

try:
    from scapy.all import *
except ImportError:
    os.system("source /home/kim/tsn_venv/bin/activate && pip install scapy")
    from scapy.all import *

def check_wireshark_version():
    """Check Wireshark version and R-TAG support"""
    print("🔍 Checking Wireshark R-TAG support...")
    try:
        result = os.popen("wireshark --version").read()
        print(f"Wireshark version: {result.split()[1] if len(result.split()) > 1 else 'unknown'}")
        print("Expected R-TAG fields:")
        print("  • ieee8021cb.etype (EtherType)")
        print("  • ieee8021cb.reserved (Reserved)")
        print("  • ieee8021cb.seq (Sequence)")
        print("")
    except:
        print("Could not determine Wireshark version")

def create_proper_rtag_frame(seq_num, next_protocol=0x0800):
    """Create R-TAG frame that Wireshark can properly dissect"""
    
    # Ethernet header
    dst_mac = bytes.fromhex('ffffffffffff')  # Broadcast
    try:
        src_mac_str = get_if_hwaddr("enp2s0").replace(':', '')
        src_mac = bytes.fromhex(src_mac_str)
    except:
        src_mac = bytes.fromhex('68050cabd96e7')
    
    # VLAN tag: 0x8100 + Priority(3) + VLAN(100)
    vlan_tci = (3 << 13) | 100
    vlan_tag = struct.pack('!HH', 0x8100, vlan_tci)
    
    # R-TAG structure according to IEEE 802.1CB
    # Note: In VLAN frames, R-TAG replaces the normal EtherType position
    rtag_ethertype = 0xF1C1
    rtag_reserved = 0x0000
    rtag_sequence = seq_num
    
    # R-TAG: EtherType + Reserved + Sequence + Next Protocol
    rtag_header = struct.pack('!HHHH', 
                             rtag_ethertype,  # 0xF1C1
                             rtag_reserved,   # 0x0000
                             rtag_sequence,   # sequence number
                             next_protocol)   # next protocol (IP = 0x0800)
    
    # IP packet payload
    payload_text = f"Official R-TAG Test #{seq_num}"
    
    # Build minimal IP/UDP packet
    ip_header = struct.pack('!BBHHHBBH4s4s',
        0x45,  # Version + IHL
        0x00,  # TOS
        20 + 8 + len(payload_text),  # Total length
        seq_num,  # ID
        0x4000,  # Flags + Fragment
        64,    # TTL
        17,    # Protocol (UDP)
        0,     # Checksum (simplified)
        socket.inet_aton("192.168.100.1"),  # Src IP
        socket.inet_aton("192.168.100.2")   # Dst IP
    )
    
    udp_header = struct.pack('!HHHH',
        12345,  # Src port
        54321,  # Dst port
        8 + len(payload_text),  # Length
        0       # Checksum (simplified)
    )
    
    # Complete frame
    frame = (dst_mac + src_mac + vlan_tag + rtag_header + 
             ip_header + udp_header + payload_text.encode())
    
    return frame

def create_reference_vlan_frame(seq_num):
    """Create reference VLAN frame without R-TAG"""
    
    dst_mac = bytes.fromhex('ffffffffffff')
    try:
        src_mac_str = get_if_hwaddr("enp2s0").replace(':', '')
        src_mac = bytes.fromhex(src_mac_str)
    except:
        src_mac = bytes.fromhex('68050cabd96e7')
    
    # VLAN tag
    vlan_tci = (3 << 13) | 100
    vlan_tag = struct.pack('!HH', 0x8100, vlan_tci)
    
    # Direct IP EtherType (no R-TAG)
    ip_ethertype = struct.pack('!H', 0x0800)
    
    # Simple IP/UDP payload
    payload_text = f"Reference VLAN #{seq_num}"
    
    ip_udp = (
        b'\x45\x00'  # IP version, header length, TOS
        + struct.pack('!H', 20 + 8 + len(payload_text))  # Total length
        + struct.pack('!H', seq_num)  # ID
        + b'\x40\x00\x40\x11\x00\x00'  # Flags, TTL, protocol, checksum
        + socket.inet_aton("192.168.100.1")  # Source IP
        + socket.inet_aton("192.168.100.2")  # Dest IP
        + struct.pack('!HHHH', 12345, 54321, 8 + len(payload_text), 0)  # UDP
        + payload_text.encode()
    )
    
    frame = dst_mac + src_mac + vlan_tag + ip_ethertype + ip_udp
    return frame

def send_official_rtag_test():
    """Send R-TAG frames designed for Wireshark official dissector"""
    
    print("=" * 80)
    print("🏛️  WIRESHARK OFFICIAL 802.1CB R-TAG TEST")
    print("=" * 80)
    
    check_wireshark_version()
    
    print("📋 Test Design:")
    print("  • Proper R-TAG structure for official Wireshark dissector")
    print("  • EtherType 0xF1C1 in correct position")
    print("  • Reserved field: 0x0000")
    print("  • Sequence numbers: 1-5 with duplicates")
    print("")
    
    # Create raw socket
    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind(("enp2s0", 0))
    except PermissionError:
        print("❌ Need root permissions")
        return
    except Exception as e:
        print(f"❌ Socket error: {e}")
        return
    
    try:
        # Phase 1: Reference frames
        print("📤 Phase 1: Reference VLAN frames (no R-TAG)")
        for i in range(3):
            frame = create_reference_vlan_frame(i + 1)
            sock.send(frame)
            print(f"   ✓ Reference #{i+1} sent ({len(frame)} bytes)")
            time.sleep(0.3)
        
        print("")
        
        # Phase 2: Official R-TAG frames
        print("📤 Phase 2: Official R-TAG frames with FRER")
        for i in range(5):
            seq_num = i + 1
            frame = create_proper_rtag_frame(seq_num)
            
            # Show R-TAG details
            rtag_bytes = struct.pack('!HHH', 0xF1C1, 0x0000, seq_num)
            print(f"   🏷️  Seq {seq_num}: R-TAG = {rtag_bytes.hex()}")
            
            # Send original
            sock.send(frame)
            print(f"   ✓ Original sent ({len(frame)} bytes)")
            
            time.sleep(0.001)
            
            # Send duplicate (FRER replication)
            sock.send(frame)
            print(f"   ✓ Duplicate sent")
            print("")
            
            time.sleep(0.5)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        sock.close()
    
    print("=" * 80)
    print("✅ OFFICIAL R-TAG TEST COMPLETED")
    print("=" * 80)
    print("")
    print("🔍 WIRESHARK ANALYSIS WITH OFFICIAL DISSECTOR:")
    print("")
    print("📊 Display Filters (Official):")
    print("  • All R-TAG packets: ieee8021cb")
    print("  • Specific sequence: ieee8021cb.seq == 3")
    print("  • All test traffic: vlan.id == 100")
    print("  • EtherType filter: ieee8021cb.etype == 0xf1c1")
    print("")
    print("🎯 Expected Protocol Tree:")
    print("  • Ethernet II")
    print("  • 802.1Q Virtual LAN")
    print("  • IEEE 802.1CB Redundancy Tag ← Should appear!")
    print("    - Type: 0xf1c1")
    print("    - Reserved: 0x0000")
    print("    - SEQ: [sequence number]")
    print("  • Internet Protocol Version 4")
    print("  • User Datagram Protocol")
    print("")
    print("🧩 Packet Structure Verification:")
    for i in range(1, 6):
        rtag_hex = struct.pack('!HHH', 0xF1C1, 0x0000, i).hex()
        print(f"  Seq {i}: Look for {rtag_hex} in hex view")
    print("")
    print("💡 Each sequence should appear exactly twice!")
    print("💡 Wireshark should now show 'IEEE 802.1CB' in Protocol column!")

if __name__ == "__main__":
    send_official_rtag_test()