"""DigiKey in-stock keyword search with required parameter matches.
Usage: dk_find.py "<keywords>" 'Param=substr' ... -> top in-stock matches by quantity"""
import sys,os,json
argv=sys.argv[1:]; sys.argv=["x"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"stock.py")).read().split('for kw in sys.argv')[0])
H={"Authorization":"Bearer "+digikey_token(),"X-DIGIKEY-Client-Id":os.environ["DIGIKEY_CLIENT_ID"],"X-DIGIKEY-Locale-Site":"US","X-DIGIKEY-Locale-Currency":"USD"}
kw,conds=argv[0],[a.split("=",1) for a in argv[1:]]
rows=[]
for off in range(0,300,50):
    d=post("https://api.digikey.com/products/v4/search/keyword",{"Keywords":kw,"Limit":50,"Offset":off,"FilterOptionsRequest":{"SearchOptions":["InStock"]}},H)
    ps=d.get("Products") or []
    for p in ps:
        pr={pa["ParameterText"]:pa["ValueText"] for pa in p["Parameters"]}
        if all(v in (pr.get(k) or "") for k,v in conds) and p["ProductStatus"]["Status"]=="Active":
            rows.append((p.get("QuantityAvailable") or 0,p["ManufacturerProductNumber"],p["Manufacturer"]["Name"],p.get("UnitPrice"),"; ".join(f"{k}={pr.get(k)}" for k,_ in conds)))
    if len(ps)<50: break
for r in sorted(rows,reverse=True)[:8]: print(r)
