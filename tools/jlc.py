"""Search the JLCPCB assembly parts library (LCSC stock). Usage: python3 jlc.py <keyword> [...]"""
import json, sys, urllib.request

URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"

def jlc(kw, page=1, size=25):
    req = urllib.request.Request(URL, data=json.dumps({"keyword": kw, "currentPage": page, "pageSize": size}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return ((json.load(urllib.request.urlopen(req, timeout=60)).get("data") or {}).get("componentPageInfo") or {})

for kw in sys.argv[1:]:
    info = jlc(kw)
    print(f"== {kw} ({info.get('total')} results)")
    for c in info.get("list") or []:
        print(f"  {c.get('componentCode')} | {c.get('componentModelEn')} | {c.get('componentTypeEn')} | stock {c.get('stockCount')} | {(c.get('describe') or '')[:80]}")
