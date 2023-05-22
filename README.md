# picopanel
MQTT fed RGB LED Panel via Raspberry Pico W

This repo contains the CircuitPython code (easily customisable), design and 3D files for a rear stand-off (P3 panel size), and some very efficient fonts.
![Screenshot](PicoPanel20230522.jpg)

```mermaid
flowchart LR
    I[Internet] --- | | R[Node-Red]
    L[LAN] --- R
    Z[Zigbee2MQTT] --- M
    R ---| |M((MQTT Broker))
    M ---| |P[PicoPanel]
```
