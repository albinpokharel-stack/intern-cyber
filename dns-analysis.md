Transaction ID: 0x1032

frame.time_relative == 0.000000
Frame Number: 1Internet Protocol Version 4, Src: 192.168.170.8, Dst: 192.168.170.20
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
    Total Length: 56
    Identification: 0x0000 (0)
    10. .... = Flags: 0x2, Don't fragment
    ...0 0000 0000 0000 = Fragment Offset: 0
    Time to Live: 64
    Protocol: UDP (17)
    Header Checksum: 0x6547 [validation disabled]
    [Header checksum status: Unverified]
    Source Address: 192.168.170.8
    Destination Address: 192.168.170.20
    [Stream index: 0]
User Datagram Protocol, Src Port: 32795, Dst Port: 53
    Source Port: 32795
    Destination Port: 53
    Length: 36
    Checksum: 0x85ed [unverified]
    [Checksum Status: Unverified]
    [Stream index: 0]
    [Stream Packet Number: 1]
    [Timestamps]
    UDP payload (28 bytes)

ip.dst == 192.168.170.20
ip.src == 192.168.170.8
frame.len == 70
_ws.col.info == "Standard query 0x1032 TXT google.com"



Transaction ID: 0x1032
Frame Number: 2

Internet Protocol Version 4, Src: 192.168.170.20, Dst: 192.168.170.8
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
    Total Length: 84
    Identification: 0xcbec (52204)
    0. .... = Flags: 0x0
    ...0 0000 0000 0000 = Fragment Offset: 0
    Time to Live: 128
    Protocol: UDP (17)
    Header Checksum: 0x993e [validation disabled]
    [Header checksum status: Unverified]
    Source Address: 192.168.170.20
    Destination Address: 192.168.170.8
    [Stream index: 0]
User Datagram Protocol, Src Port: 53, Dst Port: 32795
    Source Port: 53
    Destination Port: 32795
    Length: 64
    Checksum: 0xc725 [unverified]
    [Checksum Status: Unverified]
    [Stream index: 0]
    [Stream Packet Number: 2]
    [Timestamps]
    UDP payload (56 bytes)

ip.src == 192.168.170.20
ip.dst == 192.168.170.8a
frame.len == 98