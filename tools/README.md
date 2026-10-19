# Tools

| Script | Use |
|---|---|
| `stock.py <keyword>…` | Search DigiKey and Mouser for stock and price |
| `dk_cat.py <categoryId> <out.json>` | Dump every in-stock DigiKey product in a category |
| `dk_pn.py <MPN>…` | Exact DigiKey part lookup: stock, status, key specs |
| `jlc.py <keyword>…` | Search the JLCPCB assembly library (LCSC stock); no key needed |
| `freq.py` | Parse DigiKey frequency strings (`covers_fm()`) |
| `shot.cjs <page.html> <out.png>` | Screenshot a wiring diagram with Playwright |

API keys come from environment variables (`DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`, `MOUSER_API_KEY`). Never commit keys.
DigiKey limits a search to offset + limit ≤ 300, so `dk_cat.py` can truncate large categories.
`shot.cjs` loads Playwright from `PLAYWRIGHT_MODULE` if set, else `playwright`, and needs absolute paths.
