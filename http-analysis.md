frame.number == 29
frame.time_relative == 52529.668559538
ip.src == 127.0.0.1
ip.dst == 127.0.0.1
frame.len == 392
_ws.col.protocol == "HTTP"
_ws.col.info == "GET /my/foobar HTTP/1.1 "
Hypertext Transfer Protocol
    GET /my/foobar HTTP/1.1\r\n
        Request Method: GET
        Request URI: /my/foobar
        Request Version: HTTP/1.1
    Host: 127.0.0.1\r\n
    User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0\r\n
    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n
    Accept-Language: en-US,en;q=0.5\r\n
    Accept-Encoding: gzip, deflate\r\n
    Connection: keep-alive\r\n
    Upgrade-Insecure-Requests: 1\r\n
    \r\n
    [Full request URI: http://127.0.0.1/my/foobar]
Internet Protocol Version 4, Src: 127.0.0.1, Dst: 127.0.0.1


Transmission Control Protocol, Src Port: 47864, Dst Port: 80, Seq: 1, Ack: 1, Len: 326
    Source Port: 47864
    Destination Port: 80
    [Stream index: 5]
    [Stream Packet Number: 1]
    [Conversation completeness: Incomplete (8)]
    [TCP Segment Len: 326]
    Sequence Number: 1    (relative sequence number)
    Sequence Number (raw): 2929482010
    [Next Sequence Number: 327    (relative sequence number)]
    Acknowledgment Number: 1    (relative ack number)
    Acknowledgment number (raw): 4048806761
    1000 .... = Header Length: 32 bytes (8)
    Flags: 0x018 (PSH, ACK)
    Window: 342
    [Calculated window size: 342]
    [Window size scaling factor: -1 (unknown)]
    Checksum: 0xff6e [unverified]
    [Checksum Status: Unverified]
    Urgent Pointer: 0
    Options: (12 bytes), No-Operation (NOP), No-Operation (NOP), Timestamps
    [Timestamps]
    [Client Contiguous Streams: 1]
    [Server Contiguous Streams: 1]
    TCP payload (326 bytes)
Frame 29: Packet, 392 bytes on wire (3136 bits), 392 bytes captured (3136 bits) on interface lo, id 0
    Section number: 1
    Interface id: 0 (lo)
    Encapsulation type: Ethernet (1)
    Arrival Time: Mar 28, 2018 22:58:11.635937777 Nepal Standard Time
    UTC Arrival Time: Mar 28, 2018 17:13:11.635937777 UTC
    Epoch Arrival Time: 1522257191.635937777
    [Time shift for this packet: 0.000000000 seconds]
    [Time delta from previous captured frame: 8.028903 milliseconds]
    [Time delta from previous displayed frame: 8.514354 milliseconds]
    [Time since reference or first frame: 14 hours, 35 minutes, 29.668559538 seconds]
    Frame Number: 29
    Frame Length: 392 bytes (3136 bits)
    Capture Length: 392 bytes (3136 bits)
    [Frame is marked: False]
    [Frame is ignored: False]
    [Protocols in frame: eth:ethertype:ip:tcp:http]
    Character encoding: ASCII (0)
    [Coloring Rule Name: HTTP]
    [Coloring Rule String: http || tcp.port == 80 || http2]


Internet Protocol Version 4, Src: 127.0.0.1, Dst: 127.0.0.1
    0100 .... = Version: 4
    .... 0101 = Header Length: 20 bytes (5)
    Differentiated Services Field: 0x00 (DSCP: CS0, ECN: Not-ECT)
    Total Length: 378
    Identification: 0xe8c6 (59590)
    10. .... = Flags: 0x2, Don't fragment
    ...0 0000 0000 0000 = Fragment Offset: 0
    Time to Live: 64
    Protocol: TCP (6)
    Header Checksum: 0x52b5 [validation disabled]
    [Header checksum status: Unverified]
    Source Address: 127.0.0.1
    Destination Address: 127.0.0.1
    [Stream index: 0]
