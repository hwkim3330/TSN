#!/usr/bin/env python3
"""
FRER Analysis Tool - Real-time duplicate detection and statistics
"""

import sys
import os
import time
import struct
from collections import defaultdict

sys.path.insert(0, '/home/kim/tsn_venv/lib/python3.12/site-packages')

try:
    from scapy.all import *
except ImportError:
    os.system("source /home/kim/tsn_venv/bin/activate && pip install scapy")
    from scapy.all import *

class FRERAnalyzer:
    """Real-time FRER frame analysis and duplicate elimination"""
    
    def __init__(self):
        self.stream_sequences = defaultdict(set)  # stream_id -> set of seen sequences
        self.packet_count = 0
        self.duplicate_count = 0
        self.unique_count = 0
        self.rtag_packets = 0
        self.sequence_stats = defaultdict(int)  # sequence -> count
        self.start_time = time.time()
        
    def analyze_packet(self, packet):
        """Analyze packet for R-TAG and FRER behavior"""
        self.packet_count += 1
        
        # Check if packet has R-TAG
        if self.has_rtag(packet):
            self.rtag_packets += 1
            sequence = self.extract_sequence(packet)
            
            if sequence is not None:
                self.sequence_stats[sequence] += 1
                
                # FRER duplicate detection (assume stream_id = 1 for simplicity)
                stream_id = 1
                
                if sequence in self.stream_sequences[stream_id]:
                    self.duplicate_count += 1
                    status = "DUPLICATE"
                    action = "ELIMINATED"
                else:
                    self.stream_sequences[stream_id].add(sequence)
                    self.unique_count += 1
                    status = "ORIGINAL"
                    action = "ACCEPTED"
                
                # Real-time output
                print(f"[{self.packet_count:3d}] Seq:{sequence:2d} | {status:9s} | {action}")
                
                # Print statistics every 10 packets
                if self.rtag_packets % 10 == 0:
                    self.print_statistics()
    
    def has_rtag(self, packet):
        """Check if packet contains R-TAG"""
        try:
            # Look for R-TAG EtherType in packet
            packet_bytes = bytes(packet)
            # Search for 0xF1C1 pattern
            for i in range(len(packet_bytes) - 1):
                if packet_bytes[i:i+2] == b'\xf1\xc1':
                    return True
            return False
        except:
            return False
    
    def extract_sequence(self, packet):
        """Extract sequence number from R-TAG"""
        try:
            packet_bytes = bytes(packet)
            # Find R-TAG EtherType position
            for i in range(len(packet_bytes) - 5):
                if packet_bytes[i:i+2] == b'\xf1\xc1':
                    # R-TAG structure: EtherType(2) + Reserved(2) + Sequence(2)
                    if i + 6 <= len(packet_bytes):
                        reserved = struct.unpack('!H', packet_bytes[i+2:i+4])[0]
                        sequence = struct.unpack('!H', packet_bytes[i+4:i+6])[0]
                        if reserved == 0x0000:  # Validate reserved field
                            return sequence
            return None
        except:
            return None
    
    def print_statistics(self):
        """Print current FRER statistics"""
        runtime = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("🔍 FRER ANALYSIS STATISTICS")
        print("="*60)
        print(f"Runtime: {runtime:.1f} seconds")
        print(f"Total packets analyzed: {self.packet_count}")
        print(f"R-TAG packets found: {self.rtag_packets}")
        print(f"Unique frames accepted: {self.unique_count}")
        print(f"Duplicate frames eliminated: {self.duplicate_count}")
        
        if self.rtag_packets > 0:
            elimination_rate = (self.duplicate_count / self.rtag_packets) * 100
            print(f"Elimination rate: {elimination_rate:.1f}%")
        
        print("\nSequence number distribution:")
        for seq in sorted(self.sequence_stats.keys()):
            count = self.sequence_stats[seq]
            status = "✓ Expected" if count == 2 else f"⚠ Unexpected ({count})"
            print(f"  Seq {seq:2d}: {count:2d} packets | {status}")
        
        print("="*60 + "\n")

def run_realtime_analysis():
    """Run real-time FRER analysis"""
    
    print("=" * 70)
    print("🔬 REAL-TIME FRER ANALYSIS")
    print("=" * 70)
    print("Monitoring interface: enp2s0")
    print("Filter: VLAN 100 packets")
    print("Press Ctrl+C to stop and see final statistics")
    print("")
    print("Legend:")
    print("  ORIGINAL  = First time seeing this sequence (ACCEPTED)")
    print("  DUPLICATE = Already seen this sequence (ELIMINATED)")
    print("")
    
    analyzer = FRERAnalyzer()
    
    def packet_handler(packet):
        analyzer.analyze_packet(packet)
    
    try:
        # Capture on enp2s0 with VLAN 100 filter
        sniff(iface="enp2s0", 
              filter="vlan 100",
              prn=packet_handler,
              store=False)
              
    except KeyboardInterrupt:
        print("\n🛑 Analysis stopped by user")
        analyzer.print_statistics()
        
        # Generate summary report
        print("\n📊 FRER TEST SUMMARY:")
        print(f"Expected behavior: Each sequence should appear exactly 2 times")
        print(f"FRER effectiveness: {len(analyzer.stream_sequences[1])} unique sequences identified")
        
        # Check for perfect FRER behavior
        perfect_frer = True
        for seq, count in analyzer.sequence_stats.items():
            if count != 2:
                perfect_frer = False
                break
        
        if perfect_frer and analyzer.duplicate_count > 0:
            print("✅ Perfect FRER behavior detected!")
            print("   - All duplicates correctly identified")
            print("   - Exactly 2 copies of each sequence")
        else:
            print("⚠ Non-standard behavior detected")

def send_test_sequence():
    """Send a fresh test sequence for analysis"""
    
    print("🚀 Sending fresh test sequence for real-time analysis...")
    
    # Import the working function from our previous script
    import socket
    
    def create_proper_rtag_frame(seq_num, next_protocol=0x0800):
        """Create R-TAG frame that works with Wireshark"""
        
        dst_mac = bytes.fromhex('ffffffffffff')
        try:
            src_mac_str = get_if_hwaddr("enp2s0").replace(':', '')
            src_mac = bytes.fromhex(src_mac_str)
        except:
            src_mac = bytes.fromhex('68050cabd96e7')
        
        vlan_tci = (3 << 13) | 100
        vlan_tag = struct.pack('!HH', 0x8100, vlan_tci)
        
        rtag_header = struct.pack('!HHHH', 0xF1C1, 0x0000, seq_num, next_protocol)
        
        payload_text = f"Analysis Test #{seq_num}"
        
        ip_header = struct.pack('!BBHHHBBH4s4s',
            0x45, 0x00, 20 + 8 + len(payload_text), seq_num, 0x4000, 64, 17, 0,
            socket.inet_aton("192.168.100.1"), socket.inet_aton("192.168.100.2"))
        
        udp_header = struct.pack('!HHHH', 12345, 54321, 8 + len(payload_text), 0)
        
        frame = (dst_mac + src_mac + vlan_tag + rtag_header + 
                 ip_header + udp_header + payload_text.encode())
        
        return frame
    
    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind(("enp2s0", 0))
        
        print("Sending 3 sequences with duplicates...")
        for i in range(3):
            seq_num = i + 10  # Use different sequence numbers
            frame = create_proper_rtag_frame(seq_num)
            
            print(f"📤 Sending sequence {seq_num}...")
            
            # Send original
            sock.send(frame)
            time.sleep(0.01)
            
            # Send duplicate
            sock.send(frame)
            time.sleep(0.5)
            
        sock.close()
        print("✅ Test sequence sent!")
        
    except Exception as e:
        print(f"❌ Error sending test: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        send_test_sequence()
    else:
        run_realtime_analysis()