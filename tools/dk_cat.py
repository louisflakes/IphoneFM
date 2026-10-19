"""Pull every in-stock product in a DigiKey category; save JSON. Usage: dk_cat.py <categoryId> <outfile>"""
import sys, json
argv = sys.argv[1:]
sys.argv = ["x"]
exec(open(__file__.replace("dk_cat.py", "stock.py")).read().split("for kw in sys.argv")[0])

cat, out = argv
H = {"Authorization": "Bearer " + digikey_token(), "X-DIGIKEY-Client-Id": os.environ["DIGIKEY_CLIENT_ID"],
     "X-DIGIKEY-Locale-Site": "US", "X-DIGIKEY-Locale-Currency": "USD"}
items, off = [], 0
while True:
    d = post("https://api.digikey.com/products/v4/search/keyword",
             {"Keywords": "", "Limit": 50, "Offset": off,
              "FilterOptionsRequest": {"CategoryFilter": [{"Id": cat}], "SearchOptions": ["InStock"]}}, H)
    if "_error" in d:
        print("error", d); break
    prods = d.get("Products") or []
    items += prods
    total = d.get("ProductsCount") or 0
    off += 50
    if not prods or off >= total:
        break
json.dump(items, open(out, "w"))
print(cat, "in-stock products:", len(items), "of", total)
