"""Small text/provenance helpers shared by the public offline tools."""
import csv,hashlib,json,math,re
from pathlib import Path

MISSING='MISSING'
def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def number(value):
 try:
  text=str(value).strip().replace('D','E').replace('d','e')
  if not re.search('[Ee]',text):text=re.sub(r'(?<=\d)([+-]\d{3})$',r'E\1',text)
  n=float(text)
  return n if math.isfinite(n) else None
 except (TypeError,ValueError):return None
def read_csv(path):
 if not Path(path).exists():return []
 with Path(path).open() as f:return [r for r in csv.DictReader(f) if None not in r and all(v is not None for v in r.values())]
def write_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 def clean(v):
  if v is None:return MISSING
  if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
  if isinstance(v,(list,tuple)):return [clean(x) for x in v]
  return v
 with path.open('x') as f:json.dump(clean(value),f,indent=2,allow_nan=False);f.write('\n')
def write_csv(path,rows):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);keys=list(dict.fromkeys(k for row in rows for k in row))
 with path.open('x',newline='') as f:
  w=csv.DictWriter(f,keys,restval=MISSING);w.writeheader();w.writerows(rows)
def controls(path):
 result={}
 if Path(path).exists():
  for line in Path(path).read_text().splitlines():
   words=line.split('#',1)[0].split()
   if words:result[words[0].upper()]=' '.join(words[1:])
 return result
