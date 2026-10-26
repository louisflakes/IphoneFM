"""Exact-part DigiKey lookup. Usage: python3 dk_pn.py MPN [MPN ...] -> MPN | qty | status | price | key params"""
import sys,os,json,urllib.request,urllib.parse
argv=sys.argv[1:]; sys.argv=["x"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"stock.py")).read().split('for kw in sys.argv')[0])
H={"Authorization":"Bearer "+digikey_token(),"X-DIGIKEY-Client-Id":os.environ["DIGIKEY_CLIENT_ID"],"X-DIGIKEY-Locale-Site":"US","X-DIGIKEY-Locale-Currency":"USD","Accept":"application/json"}
KEYS=["Capacitance","Tolerance","Voltage - Rated","Temperature Coefficient","Resistance","Power (Watts)","Package / Case","ESR (Equivalent Series Resistance)","Inductance"]
for pn in argv:
    try:
        p=json.load(urllib.request.urlopen(urllib.request.Request("https://api.digikey.com/products/v4/search/"+urllib.parse.quote(pn)+"/productdetails",headers=H),timeout=60))["Product"]
    except Exception as e:
        print(f"{pn} | ERR {getattr(e,'code',e)}"); continue
    pr={pa["ParameterText"]:pa["ValueText"] for pa in p["Parameters"]}
    print(f"{p['ManufacturerProductNumber']} | qty {p.get('QuantityAvailable')} | {p['ProductStatus']['Status']} | ${p.get('UnitPrice')} | "+" · ".join(pr[k] for k in KEYS if pr.get(k) not in (None,"-")))
