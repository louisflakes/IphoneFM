# Archived plans

These plans branched off the main design and are no longer developed. They are kept as-is for reference.
The active design is [Rev A](../rev-a/wiring.html). Plan C ([plan-c/](plan-c/)) was archived on 2026-10-21: its transmitter, the LV2285VB, is obsolete and needs a large minimum order.

| Plan | MCU | Scope | Why archived |
|---|---|---|---|
| [A](plan-a/wiring.html) | STM32F072CB | Transmit only (LV2285VB) | Adding the Si4704 receiver needed more USB buffer and RAM than the F072 has (1 KB USB packet memory) |
| [B](plan-b/wiring.html) | ATSAMD51G18A | Transmit + receive | No ROM USB bootloader in the VQFN package, so the first flash needs an SWD debugger |

Plan C keeps Plan B's headroom and adds a ROM USB bootloader, so the board is programmable over USB-C from first plug-in.
