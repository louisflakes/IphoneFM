"""Query Mouser and DigiKey APIs for stock/lifecycle. Keys come from env; never printed."""
import json, os, sys, urllib.request, urllib.parse

def post(url, body, headers, form=False):
    data = urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()
    h = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json", "Accept": "application/json"}
    h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}

def mouser(kw):
    url = "https://api.mouser.com/api/v1/search/keyword?apiKey=" + os.environ["MOUSER_API_KEY"]
    d = post(url, {"SearchByKeywordRequest": {"keyword": kw, "records": 50, "startingRecord": 0}}, {})
    if "_error" in d or d.get("Errors"):
        return [f"  ERROR {d.get('_error')} {d.get('_body') or d.get('Errors')}"]
    out = []
    for p in (d.get("SearchResults") or {}).get("Parts") or []:
        pb = p.get("PriceBreaks") or []
        price = pb[0]["Price"] if pb else "-"
        out.append(f"  {p.get('ManufacturerPartNumber')} | {p.get('Manufacturer')} | avail: {p.get('Availability') or p.get('AvailabilityInStock') or '0'} | lifecycle: {p.get('LifecycleStatus') or '-'} | 1pc: {price}")
    return out

_tok = None
def digikey_token():
    global _tok
    if _tok is None:
        d = post("https://api.digikey.com/v1/oauth2/token",
                 {"client_id": os.environ["DIGIKEY_CLIENT_ID"], "client_secret": os.environ["DIGIKEY_CLIENT_SECRET"],
                  "grant_type": "client_credentials"}, {}, form=True)
        if "access_token" not in d:
            raise SystemExit(f"DigiKey token error: {d.get('_error')} {d.get('_body')}")
        _tok = d["access_token"]
    return _tok

def digikey(kw):
    d = post("https://api.digikey.com/products/v4/search/keyword", {"Keywords": kw, "Limit": 50},
             {"Authorization": "Bearer " + digikey_token(), "X-DIGIKEY-Client-Id": os.environ["DIGIKEY_CLIENT_ID"],
              "X-DIGIKEY-Locale-Site": "US", "X-DIGIKEY-Locale-Currency": "USD"})
    if "_error" in d:
        return [f"  ERROR {d['_error']} {d['_body']}"]
    out = []
    prods = (d.get("Products") or []) + (d.get("ExactMatches") or [])
    seen = set()
    for p in prods:
        mpn = p.get("ManufacturerProductNumber")
        if mpn in seen:
            continue
        seen.add(mpn)
        status = (p.get("ProductStatus") or {}).get("Status")
        out.append(f"  {mpn} | {(p.get('Manufacturer') or {}).get('Name')} | qty: {p.get('QuantityAvailable')} | status: {status} | 1pc: {p.get('UnitPrice')}")
    return out

for kw in sys.argv[1:]:
    print(f"== {kw}")
    print(" Mouser:"); print("\n".join(mouser(kw)) or "  (no results)")
    print(" DigiKey:"); print("\n".join(digikey(kw)) or "  (no results)")
