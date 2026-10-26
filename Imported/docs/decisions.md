# Decision log

Format: ID — date — decision — reason. Don't reopen a decision without writing down the new evidence.

- **D-001 — 2026-10-18 — Defer SDR.** Wideband SDR (AD936x, LMS7002M, ESP32/MT7921 hacks) is
  too big, too expensive, needs a USB host, or has no public docs. v1 is FM only.
- **D-002 — 2026-10-18 — All-COTS is not possible at this size.** Modules that would work are
  too big (ADALM-PLUTO 117×79×24 mm) or discontinued (Adafruit Si4713). Going custom with the EE.
- **D-003 — 2026-10-18 — Path A: open MCU + separate FM transmit and receive chips.** JieLi
  Bluetooth SoCs with built-in FM transmit were rejected: closed SDK, Windows-only tools,
  confidential datasheets, and the public AC63 SDK says "AC69 without audio support".
- **D-004 — 2026-10-18 — Transmit chip: OPEN.** Jake leaned KT0803L; Claude recommended QN8027
  (better THD, RDS, has a JLCPCB footprint). Neither passes the sourcing rule today (see `bom.md`).
  Plan: dual footprint if possible; resolve at Gate 1.
- **D-005 — 2026-10-18 — MCU: ESP32-S3-MINI-1-N8.** Native USB (TinyUSB UAC2 + MIDI + CDC),
  in stock, turnkey at JLCPCB, open toolchain.
- **D-006 — 2026-10-18 — Receive: Si4735-D60.** Good sensitivity, RSSI/SNR for scanning, I²S out,
  RDS. Consigned from DigiKey (LCSC reel out of stock).
- **D-007 — 2026-10-18 — Design tool: local KiCad 10 + kicad-mcp-pro + Claude Code.** Flux.ai
  credits ran out. The old Flux project "FMTX-DEV-P3" (RP2040 + RDA5820NS + PCM5122) is reference
  only; RDA5820NS is discontinued.
- **D-008 — 2026-10-18 — GitHub repo is the source of truth** for spec, BOM, decisions, hardware and firmware.
