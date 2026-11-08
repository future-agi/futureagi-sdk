"""Discover concrete public methods bound to reviewed endpoints without importing SDKs."""
import ast,json,re,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TABLE=Path(os.environ.get('PAGINATION_TABLE',ROOT/'openapi/sdk/pagination-dialects.json'))
data=json.loads(TABLE.read_text());
for record in data['operations']:record['methods']={'python':[],'typescript':[]}
rows={(r['method'],r['path']):r for r in data['operations']}
def shape(p):return re.sub(r'\{[^}]*\}','{}',p)
shapes={(m,shape(p)):r for (m,p),r in rows.items()}
def row(m,p):return shapes.get((m.upper(),shape(p)))
def bind(r,lang,file,symbol):
 if r is None:return
 ref={'file':str(file.relative_to(ROOT)),'symbol':symbol}
 if ref not in r['methods'][lang]:r['methods'][lang].append(ref)
def snake(s):
 s=re.sub(r'([a-z0-9])([A-Z])',r'\1_\2',s)
 return re.sub(r'[^A-Za-z0-9]+','_',s).lower()
def tsname(s):
 s=re.sub(r'[^A-Za-z0-9]+','_',s)
 return re.sub(r'_([A-Za-z])',lambda m:m[1].upper(),s)
def text(n):
 if isinstance(n,ast.Constant) and isinstance(n.value,str):return n.value
 if isinstance(n,ast.JoinedStr):return ''.join(v.value if isinstance(v,ast.Constant) else '{}' for v in n.values)
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='format':return text(n.func.value)
 return ''
# All pinned operation identifiers and generated SDK aliases.
ids={};pyids={};tsids={}; public={}
for rel in ['openapi/sdk/generated/futureagi-sdk.openapi.json','openapi/catalog/source.json','openapi/tracing/source.json','openapi/connectors/fa.json','openapi/fa-mgmt/swagger.json']:
 spec=json.loads((ROOT/rel).read_text())
 for p,item in spec.get('paths',{}).items():
  for m,op in item.items():
   if m not in ['get','post']:continue
   r=row(m,p)
   if r is not None:
    oid=op['operationId'];ids[oid]=r;pyids[snake(oid)]=r;tsids[tsname(oid)]=r
for a in json.loads((ROOT/'openapi/fa-mgmt/surface.json').read_text())['operations']:
 if a['operation_id'] in ids:public[a['name']]=ids[a['operation_id']]
# Constant operation records are statically inspectable in catalog/tracing modules.
for file in (ROOT/'python/fi').rglob('*.py'):
 if any(p in file.parts for p in ['models','gateway','utils']):continue
 if 'generated/openapi_client' in str(file) and '/api/' not in str(file):continue
 source=file.read_text();tree=ast.parse(source);names={**pyids};constants={}
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom) and n.module and '.api.' in n.module:
   for alias in n.names:
    if alias.name in pyids:names[alias.asname or alias.name]=pyids[alias.name]
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   for c in ast.walk(n.value):
    if isinstance(c,ast.Dict):
     try:v=ast.literal_eval(c)
     except (ValueError,TypeError):continue
     if isinstance(v,dict) and 'method' in v and 'path' in v:
      r=row(v['method'],v['path'])
      if r:constants[n.targets[0].id]=r
 def walk(n,prefix=''):
  for child in ast.iter_child_nodes(n):
   if isinstance(child,ast.ClassDef):walk(child,prefix+child.name+'.');continue
   if not isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
   if child.name.startswith('_'):continue
   found=[]
   if 'generated/openapi_client/api/' in str(file) and file.stem in pyids and child.name in ['sync','sync_detailed','asyncio','asyncio_detailed']:
    found.append(pyids[file.stem])
   else:
    for call in ast.walk(child):
     if not isinstance(call,ast.Call):continue
     fn=ast.unparse(call.func)
     if fn.endswith('._raw_request') and len(call.args)>1:
      found.append(row(text(call.args[0]),text(call.args[1])))
     # Generated call references (including aliased imports).
     for a in call.args[:2]:
      if isinstance(a,ast.Attribute):found.append(names.get(ast.unparse(a.value)))
      elif isinstance(a,ast.Name):found.append(names.get(a.id) or constants.get(a.id))
      elif isinstance(a,ast.Constant) and isinstance(a.value,str):found.append(public.get(a.value) or ids.get(a.value))
      elif isinstance(a,ast.Subscript):found.append(ids.get(text(a.slice)))
   if child.name=='spans_by_trace':found.append(rows.get(('GET','/tracer/observation-span/list_spans_observe/')))
   for r in found:bind(r,'python',file,prefix+child.name)
 walk(tree)
# Generated integration modules use operation IDs; no direct endpoint strings in facades.
# TypeScript facade methods are emitted at two-space indentation, and low-level functions
# at column zero. Resolve references from imports/const operation records, never method names.
for file in (ROOT/'typescript/futureagi/src').rglob('*.ts'):
 if any(p in file.parts for p in ['__tests__','node_modules','gateway-client']):continue
 if file.name in ['types.gen.ts','index.ts'] and '/generated/openapi/' in str(file):continue
 source=file.read_text();constants={}
 for match in re.finditer(r'^const (\w+): CatalogOperation = (.+);$',source,re.M):
  v=json.loads(match[2]);constants[match[1]]=row(v['method'],v['path'])
 classes=list(re.finditer(r'^export class (\w+)',source,re.M))
 if file.name=='sdk.gen.ts':
  for match in re.finditer(r'^export const (\w+)\b',source,re.M):bind(tsids.get(match[1]),'typescript',file,match[1])
  continue
 for i,c in enumerate(classes):
  end=classes[i+1].start() if i+1<len(classes) else len(source)
  chunk=source[c.start():end]
  methods=list(re.finditer(r'^  (?:(?:public|private|protected|async|static|override) )*(\w+)\s*\(',chunk,re.M))
  for j,m in enumerate(methods):
   if m[1]=='constructor':continue
   body=chunk[m.start():methods[j+1].start() if j+1<len(methods) else len(chunk)]
   # Strip comments to avoid accidental reference matches from examples/JSDoc.
   body=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
   found=[]
   for oid in re.findall(r'\b(?:generatedSdk|dataSdk|sdk)\.(\w+)',body):found.append(tsids.get(oid))
   for const in re.findall(r'this\.call\((\w+)',body):found.append(constants.get(const))
   for name in re.findall(r'(?:this\.call(?:<[^;]*?>)?\(|\[)["\']([^"\']+)["\']',body):found.append(public.get(name) or ids.get(name))
   for method,path in re.findall(r'["\'](GET|POST)["\'],\s*[`"\']([^`"\']+)[`"\']',body):found.append(row(method,re.sub(r'\$\{.*?\}','{}',path)))
   if m[1]=='spansByTrace':found.append(rows.get(('GET','/tracer/observation-span/list_spans_observe/')))
   for r in found:bind(r,'typescript',file,c[1]+'.'+m[1])
for r in rows.values():
 for lang in r['methods']:r['methods'][lang].sort(key=lambda a:(a['file'],a['symbol']))
 for lang, refs in r['methods'].items():
  if not refs and lang not in r.get('not_offered', {}):raise ValueError(f'Missing {lang} methods: {r["method"]} {r["path"]}')
result=json.dumps(data,indent=2)+'\n'
if '--check' in sys.argv:
 if result!=TABLE.read_text():raise SystemExit('Pagination method inventory is stale; run scripts/pagination_inventory.py')
else:TABLE.write_text(result)
print('Methods', {lang:sum(len(r['methods'][lang]) for r in rows.values()) for lang in ['python','typescript']})
