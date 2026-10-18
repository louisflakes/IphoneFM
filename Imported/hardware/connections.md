# Intended connections (netlist contract)

To be filled at Gate 2. The KiCad netlist is diffed against this file after every schematic
change. One line per net: `NET_NAME: U1.pin, U2.pin, ...`

## Blocks (draft)

- USB-C receptacle → ESP32-S3 USB D+/D− (GPIO19/20), VBUS → 3.3 V LDO(s)
- ESP32-S3 I²S out → PCM5102A → (analog L/R, level set for transmitter input) → FM transmit IC
- FM transmit IC RF out → π-attenuator (0 Ω default) → low-pass filter → U.FL test point → antenna
- Antenna (receive) → Si4735 FMI
- Si4735 I²S out → ESP32-S3 I²S in (to USB mic)
- Shared I²C: ESP32-S3 ↔ FM transmit IC ↔ Si4735 (check addresses don't collide)
- Si4735 RCLK: 32.768 kHz crystal or clock from ESP32-S3
- BOOT + RESET buttons, SWD/JTAG pads, status LED
