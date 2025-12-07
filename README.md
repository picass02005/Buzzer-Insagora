# General description

This project is a request from Insagora club, realised in associon with Club Robot and Club Info.

It consists of a set of buzzers (ESP-32 based) communicating with a PC backend and a web frontend.

# Contacts

Club Info: <[club.info@amicale-insat.fr](mailto:club.info@amicale-insat.fr)><br>
Club Robot: <[club.robot@amicale-insat.fr](mailto:club.robot@amicale-insat.fr)>

Main developper: Clément Duran <[clementduran0@gmail.com](mailto:clementduran0@gmail.com)>

# Manual

> [!TOOD]

# Technical specifications

## Hardware

> [!TOOD]

## Software
### Communication diagram

```mermaid
flowchart LR
    A[Computer] <-->|Bluetooth Low Energy| B[Buzzer-1<br>&quot;Gateway&quot;]
    subgraph Buzzer network
        B <-->|ESP-Now| C[Buzzer-2]
        B <-->|ESP-Now| D[Buzzer-3]
        B <-->|ESP-Now| E[...]
    end
```

### Computer to gateway communication

All packets sent from the computer follow the same general PDU:

```mermaid
packet
0-6: "Destination adress"
7-31: "Command (separated from data by a space, variable length)"
32-63: "Data (Optional, variable length)"
64-95: "Padding (Optional, total length is 240 bytes)"
```

Data are raw bytes.
Broadcast address is `\xFF\xFF\xFF\xFF\xFF\xFF` (or more human-readable `ff:ff:ff:ff:ff:ff`).

### Gateway to computer communication

Communication from gateway to computer isn't normalized.
Max size is 247 bytes.

It is made from `data` field of a `ESPNowMessage` where `fwd_ble` is `1`.

### Between multiple ESP

All packets through the ESP-NOW network are currently sent to broadcast address (`ff:ff:ff:ff:ff:ff`).

Each of them is a `ESPNowMessage`.

Structure of `ESPNowMessage`:
- `char fwd_ble`: Represent if the message should be forwarded through BLE network when it reaches the gateway.<br>
To forward it, set its value to `1`, else set it to `0`.
- `char target[6]`: Contain the target ESP MAC address for this packet.<br>
Set it to `{0xff, 0xff, 0xff, 0xff, 0xff, 0xff}` for a broadcast message.<br>
For this purpose, you can use the `broadcastAddress` constant.
- `char data[240]`: The raw data of this packet.<br>
If you're sending a command and its data, separate them with a space.

### Example communication

In the following example, we suppose we have a generic `PING` command where respond is in the form `PONG [destination MAC address]`

#### Example 1: direct command to gateway

```mermaid
sequenceDiagram
    participant C as Computer
    box Purple ESP-NOW network
        participant G as Buzzer 1 (Gateway)<br>aa:aa:aa:aa:aa:aa
        participant B2 as Buzzer 2<br>bb:bb:bb:bb:bb:bb
        participant B3 as Buzzer 3<br>cc:cc:cc:cc:cc:cc
    end

    C->>G: Target: aa:aa:aa:aa:aa:aa<br>Data: PING
    activate G
    G->>C: Data: PONG aa:aa:aa:aa:aa:aa
    deactivate G
```

#### Example 2: command to a specific buzzer

```mermaid
sequenceDiagram
    participant C as Computer
    box Purple ESP-NOW network
        participant G as Buzzer 1 (Gateway)<br>aa:aa:aa:aa:aa:aa
        participant B2 as Buzzer 2<br>bb:bb:bb:bb:bb:bb
        participant B3 as Buzzer 3<br>cc:cc:cc:cc:cc:cc
    end

    C->>G: Target: bb:bb:bb:bb:bb:bb<br>Data: PING
    G->>B2: Target: bb:bb:bb:bb:bb:bb<br>Data: PING<br>Fwd_ble: 0
    activate B2
    B2->>G: Target: aa:aa:aa:aa:aa:aa<br>Data: PONG bb:bb:bb:bb:bb:bb<br>Fwd_ble: 1
    deactivate B2
    G->>C: Data: PONG bb:bb:bb:bb:bb:bb
```

#### Example 3: command to every buzzers

```mermaid
sequenceDiagram
    participant C as Computer
    box Purple ESP-NOW network
        participant G as Buzzer 1 (Gateway)<br>aa:aa:aa:aa:aa:aa
        participant B2 as Buzzer 2<br>bb:bb:bb:bb:bb:bb
        participant B3 as Buzzer 3<br>cc:cc:cc:cc:cc:cc
    end
    
    C->>G: Target: ff:ff:ff:ff:ff:ff<br>Data: PING
    activate G
    par BROADCASTING
        G->>C: Data: PONG aa:aa:aa:aa:aa:aa
        deactivate G
        G->>B2: Target: ff:ff:ff:ff:ff:ff<br>Data: PING<br>Fwd_ble: 0
        activate B2
        B2 ->> G: target: aa:aa:aa:aa:aa:aa<br>Data: PONG bb:bb:bb:bb:bb:bb<br>Fwd_ble: 1
        deactivate B2
        G->>C: Data: PONG bb:bb:bb:bb:bb:bb
        G->>B3: Target: ff:ff:ff:ff:ff:ff<br>Data: PING<br>Fwd_ble: 0
        activate B3
        B3 ->> G: target: aa:aa:aa:aa:aa:aa<br>Data: PONG cc:cc:cc:cc:cc:cc<br>Fwd_ble: 1
        deactivate B3
        G->>C: Data: PONG cc:cc:cc:cc:cc:cc
    end
```


> [!TOOD]
>
> List of commands

### On board

> [!TOOD]

### Backend

> [!TOOD]

### Frontend

> [!TOOD]
