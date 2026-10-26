import re
U={'khz':1e-3,'mhz':1,'ghz':1e3}
def rng(s):
    """Return list of (lo,hi) MHz ranges parsed from a DigiKey frequency string."""
    out=[]
    for part in re.split(r',|/|;', s):
        nums=re.findall(r'([\d.]+)\s*(kHz|MHz|GHz)?', part, re.I)
        vals=[]; unit=None
        for n,u in reversed(nums):
            if u: unit=u.lower()
            if unit is None: continue
            try: vals.append(float(n)*U[unit])
            except ValueError: pass
        if not vals: continue
        out.append((min(vals),max(vals)))
    return out
def covers_fm(s, lo=88, hi=108):
    return any(a<=hi and b>=lo for a,b in rng(s))
