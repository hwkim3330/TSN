-- IEEE 802.1CB R-TAG Wireshark Dissector
-- Place this file in ~/.local/lib/wireshark/plugins/ or Wireshark plugins directory

local rtag_proto = Proto("rtag", "IEEE 802.1CB Redundancy Tag")

-- Define fields
local f_reserved = ProtoField.uint16("rtag.reserved", "Reserved", base.HEX)
local f_sequence = ProtoField.uint16("rtag.sequence", "Sequence Number", base.DEC)
local f_stream_handle = ProtoField.uint16("rtag.stream_handle", "Stream Handle", base.DEC)

-- Add fields to protocol
rtag_proto.fields = {f_reserved, f_sequence, f_stream_handle}

-- Dissector function
function rtag_proto.dissector(buffer, pinfo, tree)
    -- Check if buffer is at least 6 bytes (R-TAG length)
    if buffer:len() < 6 then
        return 0
    end
    
    -- Set protocol column
    pinfo.cols.protocol = "802.1CB"
    
    -- Add protocol tree
    local subtree = tree:add(rtag_proto, buffer(0, 6), "IEEE 802.1CB R-TAG")
    
    -- Parse fields
    local reserved = buffer(0, 2):uint()
    local sequence = buffer(2, 2):uint()
    local stream_handle = buffer(4, 2):uint()
    
    -- Add fields to tree
    subtree:add(f_reserved, buffer(0, 2))
    subtree:add(f_sequence, buffer(2, 2))
    subtree:add(f_stream_handle, buffer(4, 2))
    
    -- Set info column
    pinfo.cols.info = string.format("R-TAG Stream:%d Seq:%d", stream_handle, sequence)
    
    -- Return number of bytes consumed
    return 6
end

-- Register post-dissector to catch R-TAG after VLAN
function rtag_proto.init()
    -- Look for R-TAG after VLAN header (EtherType 0x8100)
    local eth_table = DissectorTable.get("ethertype")
    
    -- Register for custom EtherType or use post-dissector
    -- Since R-TAG doesn't have its own EtherType, we use a post-dissector
end

-- Post-dissector to find R-TAG in packets
local function rtag_postdissector(tvb, pinfo, tree)
    -- Look for VLAN packets (EtherType 0x8100)
    if tvb:len() < 22 then  -- Min packet size for Ethernet + VLAN + R-TAG
        return
    end
    
    -- Check for VLAN tag (0x8100 at offset 12)
    local ethertype = tvb(12, 2):uint()
    if ethertype == 0x8100 then
        -- VLAN header is 4 bytes, R-TAG should start at offset 18
        local rtag_offset = 18
        
        if tvb:len() >= rtag_offset + 6 then
            -- Check if this looks like an R-TAG (first 2 bytes should be 0x0000)
            local reserved = tvb(rtag_offset, 2):uint()
            if reserved == 0x0000 then
                -- Dissect R-TAG
                local rtag_tvb = tvb(rtag_offset, 6):tvb()
                rtag_proto.dissector(rtag_tvb, pinfo, tree)
            end
        end
    end
end

-- Register post-dissector
register_postdissector(rtag_postdissector)

-- Display filter examples
local info_text = [[
IEEE 802.1CB R-TAG Dissector Loaded!

Usage:
- Filter R-TAG packets: rtag
- Filter by stream: rtag.stream_handle == 1
- Filter by sequence: rtag.sequence >= 5
- Show all FRER traffic: rtag and vlan.id == 100

R-TAG Structure (6 bytes):
+0: Reserved (2 bytes, always 0x0000)
+2: Sequence Number (2 bytes)
+4: Stream Handle (2 bytes)
]]

print(info_text)