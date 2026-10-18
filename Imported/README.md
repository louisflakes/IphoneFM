# iphone-fm-radio

A USB-C iPhone accessory that transmits iPhone audio over FM (Part 15 legal) and can also
receive FM and scan for empty channels.

- Spec: [docs/spec.md](docs/spec.md)
- Parts: [docs/bom.md](docs/bom.md)
- Process: [docs/process.md](docs/process.md)
- Decisions: [docs/decisions.md](docs/decisions.md)

## Getting started (Claude Code + KiCad)

1. Install KiCad 10 and turn on the KiCad API (Preferences → Plugins).
2. Install `uv` (https://docs.astral.sh/uv/).
3. Clone this repo and open the folder in Claude Code (desktop app → Code tab).
4. Approve the `kicad` MCP server when asked, then run `/mcp` to check it shows ✔.
