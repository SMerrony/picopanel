# picopanel
MQTT fed RGB LED Panel via Raspberry Pico W

```mermaid
flowchart TD
    A[Internet] <-->| | B[Node-Red]
    B <-->| |D[Intranet]
    B -->| |C{MQTT Broker}
    C <-->| |E[PicoPanel]
```
