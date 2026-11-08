const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const net = require('node:net');
const {pathToFileURL} = require('node:url');
const OUT = process.env.SDK_OUTPUT_DIR;
const ROOT = process.env.SDK_REPO_ROOT;
if (!OUT || !ROOT) throw new Error('Explicit output and source paths required');
const BUILD = path.join(ROOT, 'typescript/futureagi/dist/gateway');
const rules = JSON.parse(fs.readFileSync(path.join(__dirname, 'shared-rules.json')));
const LABELS = ROOT+'/typescript/futureagi/gateway-client/tests/parity/onekey-labels.cjs';
const {metadataAccess,metadataAccessJustification,namedAncestry:ancestry,ancestryJustification,postHeaderBodyFailureDifference} = require(LABELS);
const PY = path.join(__dirname, 'refusal-fixtures.json');
const PY_SHA = '2c0007966cb1566173906bc676e4af8caf74f197d0aa78c1617cda7db324892b';
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const write = (name,value) => fs.writeFileSync(OUT+'/'+name,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const fixtureBytes = fs.readFileSync(PY);
assert.equal(hash(fixtureBytes),PY_SHA);
const py = JSON.parse(fixtureBytes);
const build = JSON.parse(fs.readFileSync(OUT+'/build-manifest.json'));


for(const [file,sha] of Object.entries(build.source_sha256_by_file)) assert.equal(hash(fs.readFileSync(ROOT+'/'+file)),sha);
for(const [file,sha] of Object.entries(build.build_sha256_by_file)) assert.equal(hash(fs.readFileSync(BUILD+'/'+file)),sha);
net.Socket.prototype.connect = function(){throw new Error('Network forbidden during parity generation');};
globalThis.fetch = async()=>{throw new Error('Unmocked fetch forbidden');};
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const request = {method:'POST',path:'/v1/chat/completions',body:{model:'fixture/model',messages:[]}};
const labels = {never:['never','never',false],once:['at most once after positive Retry-After','at_most_once_after_retry_after',true],after:['after positive Retry-After','after_positive_retry_after',true],status:['bounded backoff; honor Retry-After when present','configured_status_retry',null]};
const modes = ['request','requestWithResponse','requestRaw','requestStream'];
let timers = [];
const originalTimer = globalThis.setTimeout;
const originalRandom = Math.random; Math.random = () => 0.5;
globalThis.setTimeout = (fn,ms,...args)=>{timers.push(ms);queueMicrotask(()=>fn(...args));return {unref(){return this;}};};
async function observe(api,method,status,body,headers,maxRetries=5){
 let attempts=0;
 timers=[];
 const client = new api.AgentCC({apiKey:'offline-fixture',baseUrl:'https://gateway.test',maxRetries,fetch:async()=>{attempts++;return new Response(JSON.stringify(body),{status,headers});}});
 let error;
 try {await client[method](request);} catch(e){error=e;}
 assert.ok(error instanceof api.APIStatusError);
 return {error,attempts,delays:[...timers].map(x=>x/1000)};
}
function projection(delays){assert.ok(delays.length<=5);return [...delays,...Array(6-delays.length).fill(null)];}
async function row(api,policy,input){
 const metadata=input.evaluated_metadata;
 const body={error:{code:input.code,message:'offline refusal',...(metadata===null?{}:{metadata})}};
 const headers={'retry-after':'2','x-agentcc-request-id':ID,'x-agentcc-dispatched':'false'};
 const observations=[];
 for(const method of modes) observations.push(await observe(api,method,input.http_status,body,headers));
 const {error,attempts,delays}=observations[0];
 for(const observation of observations){assert.equal(observation.error.name,error.name);assert.deepEqual(observation.error.metadata,metadata);assert.equal(observation.attempts,attempts);assert.deepEqual(observation.delays,delays);}
 if(['managed_model_unpriced','managed_model_ambiguous','managed_resource_unsupported'].includes(input.code)){
  for(const valid of [false,true]){
   const raw={model:valid?'fixture/model':42,candidates:valid?['fixture/a','fixture/b']:['fixture/a',42],reason:'unpriced',unknown_key:{retained:true}};
   const guarded=api.APIStatusError.from(input.http_status,{error:{code:input.code,metadata:raw}},new Headers(headers));
   assert.deepEqual(guarded.metadata,raw);
   assert.equal(guarded.model,valid?raw.model:null);
   assert.deepEqual(guarded.candidates,valid?raw.candidates:null);
   assert.deepEqual(guarded.unpricedMetadata,valid?raw:null);
   assert.deepEqual(guarded.ambiguousMetadata,valid?raw:null);
  }
 }
 const details=policy.refusalDetails(input.http_status,body);
 assert.ok(details);
 const [retry,rule,classification] = labels[details.retry];
 // Row labels and metadata schema are fixture inputs, not inferred runtime output.
 // Validate each declared field through a sparse sentinel fixture, without widening
 // the per-variant metadata list to a union across unrelated producers.
 for(const field of input.metadata_fields){
  const getter=field.replace(/_([a-z])/g,(_,letter)=>letter.toUpperCase());
  assert.ok(getter in error);
  assert.deepEqual(error[getter],metadata?.[field]??null);
  const sentinel={...metadata,[field]:'field-preservation-probe'};
  assert.equal(api.APIStatusError.from(input.http_status,{error:{code:input.code,metadata:sentinel}},new Headers(headers)).metadata[field],sentinel[field]);
 }
 return {http_status:input.http_status,code:input.code,condition:input.condition,sdk_class:'@future-agi/sdk/gateway.'+error.name,is_subclass_of:ancestry(error),category:error.category,remedy:error.remedy,retry,retry_policy:retry,retry_rule:rule,classification_retry:classification,metadata_fields:input.metadata_fields,metadata_presence:input.metadata_presence,metadata_access:metadataAccess(input.code),evaluated_metadata:error.metadata,evaluated_retry_delays_max_five:projection(delays),evaluated_attempts_max_five:attempts,stream_attempts:observations[3].attempts,...('contract_retry' in input?{contract_retry:input.contract_retry}:{})};
}
async function bodyEvidence(api){
 const checks=[];
 const readers=[
  ['request',client=>client.request(request)],['requestWithResponse',client=>client.requestWithResponse(request)],
  ['chat.completions.create',client=>client.chat.completions.create({model:'example/model',messages:[]})],
  ['completions.create',client=>client.completions.create({model:'example/model',prompt:'example'})],
  ['embeddings.create',client=>client.embeddings.create({model:'example/model',input:'example'})],
  ['images.generate',client=>client.images.generate({model:'example/model',prompt:'example'})],
  ['rerank.rank',client=>client.rerank.rank({model:'example/model',query:'example',documents:['example']})],
  ['models.list',client=>client.models.list()],
  ['audio.transcriptions.create',client=>client.audio.transcriptions.create({model:'example/model',file:new Blob(['audio'])})],
  ['audio.translations.create',client=>client.audio.translations.create({model:'example/model',file:new Blob(['audio'])})],
 ];
 for(const [method,invoke] of readers) for(const policy of [false,true]){
  let calls=0; const errors=[];
  const response=new Response('{}',{headers:{'x-agentcc-request-id':ID,'x-agentcc-dispatched':'true','x-agentcc-client-request-id':'client'}});
  response.json=async()=>{response.headers.set('x-agentcc-request-id','mutated');throw Object.assign(new DOMException('timeout','TimeoutError'),{request:{authorization:'synthetic-sensitive-value'}});};
  const callback=new class extends api.CallbackHandler {onError(_request,error){errors.push(error);}};
  const client=new api.AgentCC({apiKey:'offline-fixture',baseUrl:'https://gateway.test',maxRetries:5,...(policy?{retryPolicy:new api.RetryPolicy({timeoutRetries:5,connectionErrorRetries:5})}:{}),callbacks:[callback],fetch:async()=>{calls++;return response;}});
  let error;try{await invoke(client);}catch(e){error=e;}
  assert.ok(error instanceof api.ResponseBodyError);assert.ok(error instanceof api.AgentCCError);assert.ok(!(error instanceof api.APIConnectionError));
  assert.equal(calls,1);assert.equal(errors.length,1);assert.equal(errors[0],error);
  assert.equal(error.gatewayEvidence,api.getGatewayEvidence(response));
  assert.deepEqual(error.gatewayEvidence,{dispatched:true,gatewayRequestId:ID,clientRequestId:'client'});
  assert.equal(error.requestId,ID);assert.equal(error.gatewayRequestId,ID);assert.equal(error.dispatched,true);assert.equal(error.clientRequestId,'client');
  assert.ok(!JSON.stringify(error).includes('synthetic-sensitive-value'));assert.equal(error.cause,undefined);
  checks.push({method,per_error_retry_policy:policy,attempts:calls,error_class:error.name,callback_same_error:true,evidence:error.gatewayEvidence,transport_cause_retained:false});
 }
 return checks;
}
async function generate(api,policy){
 const body_evidence=await bodyEvidence(api);
 const rows=[];for(const input of py.rows) rows.push(await row(api,policy,input));
 const variants=[];for(const input of py.variant_evidence) variants.push(await row(api,policy,input));
 const fallback=[];
 for(const input of py.fallback_evidence){
  const headers={'retry-after':'2'};
  if(input.request_id_present) headers['x-agentcc-request-id']='invalid-but-present';
  if(input.dispatched_header!==null) headers['x-agentcc-dispatched']=input.dispatched_header;
  const {error,delays}=await observe(api,'request',input.http_status,{},headers);
  fallback.push({http_status:input.http_status,request_id_present:input.request_id_present,dispatched_header:input.dispatched_header,gateway_request_id:error.gatewayRequestId,dispatched:error.dispatched,retry_delays_max_five:projection(delays),remedy:error.remedy});
 }
 const dispatch=py.dispatch_wire_evidence.map(input=>({raw_values_hex:input.raw_values_hex,dispatched:api.parseGatewayEvidence(input.raw_values_hex.map(hex=>['x-agentcc-dispatched',Buffer.from(hex,'hex').toString('utf8')])).dispatched}));
 const retry=py.retry_after_evidence.map(input=>({value:input.value,positive_integer_delta_seconds:(policy.positiveRetryAfter({get:()=>input.value})??null)===null?null:policy.positiveRetryAfter({get:()=>input.value})/1000}));
 const boundary=[];
 for(const seconds of [api.MAX_RETRY_AFTER_SECONDS,api.MAX_RETRY_AFTER_SECONDS+1,2147483647]){
  const headers={'retry-after':String(seconds)};
  const body={error:{code:'managed_billing_unavailable'}};
  const observed=await observe(api,'request',503,body,headers,1);
  boundary.push({retry_after_seconds:seconds,parsed_seconds:policy.positiveRetryAfter(new Headers(headers))===null?null:policy.positiveRetryAfter(new Headers(headers))/1000,attempts:observed.attempts,delays_seconds:observed.delays});
 }
 return {rows,variant_evidence:variants,fallback_evidence:fallback,dispatch_wire_evidence:dispatch,retry_after_evidence:retry,timer_boundary_evidence:boundary,response_body_evidence:body_evidence};
}
function diffRows(section,left,right){
 assert.equal(left.length,right.length);
 const differences=[];
 left.forEach((ts,i)=>{
  const python=right[i];
  assert.deepEqual(Object.keys(ts).sort(),Object.keys(python).sort());
  for(const field of Object.keys(ts)){
   try{assert.deepEqual(ts[field],python[field]);}catch{
    let justification;
    if(field==='sdk_class') justification='Language namespace only: the runtime class basename must match.';
    if(field==='is_subclass_of') justification=ancestryJustification;
    if(field==='metadata_access') justification=metadataAccessJustification(ts.code);
    if(field==='stream_attempts') justification='Inherited transport difference: TypeScript retries only the stream-opening HTTP refusal using the same bounded policy as JSON/raw; Python r6 opens streams once. Neither restarts after partial output.';
    if(!justification) throw new Error('Unexpected literal difference '+section+'['+i+'].'+field+': '+JSON.stringify([ts[field],python[field]]));
    if(field==='sdk_class') assert.equal(ts[field].split('.').at(-1),python[field].split('.').at(-1));
    if(field==='is_subclass_of') assert.deepEqual(ts[field],python[field].map(x=>x==='SDKException'?'Error':x));
    differences.push({section,index:i,http_status:ts.http_status,code:ts.code,condition:ts.condition,field,typescript:ts[field],python:python[field],justification});
   }
  }
 });
 return differences;
}

async function dispatchEvidence(api){
 const rows=[];
 for(const method of modes) for(const perError of [false,true]){
  const settings=perError?{retryPolicy:new api.RetryPolicy({connectionErrorRetries:2,timeoutRetries:2,serviceUnavailableRetries:2})}:{};
  for(const code of ['ENOTFOUND','EAI_AGAIN','ECONNREFUSED','UND_ERR_CONNECT_TIMEOUT','UND_ERR_POOL_TIMEOUT','UND_ERR_QUEUE_TIMEOUT','ECONNRESET','UND_ERR_SOCKET','UND_ERR_HEADERS_TIMEOUT','UND_ERR_BODY_TIMEOUT','ETIMEDOUT','timeout','abort','unclassified']){
   timers=[];let calls=0;
   const client=new api.AgentCC({apiKey:'offline-fixture',baseUrl:'https://gateway.test',maxRetries:2,...settings,fetch:async()=>{calls++;if(code==='timeout')throw new DOMException('timeout','TimeoutError');if(code==='abort')throw new DOMException('abort','AbortError');throw Object.assign(new TypeError('fetch failed'),code==='unclassified'?{}:{cause:Object.assign(new Error('connection failure'),{code})});}});
   let error;try{await client[method](request);}catch(e){error=e;}
   rows.push({method,per_error_retry_policy:perError,code,attempts:calls,error_class:error.name,evidence:error.gatewayEvidence,guidance:error.remedy??null,retry_sleeps:timers.length});
  }
  for(const code of [null,'future_code','managed_billing_unavailable']) for(const dispatched of [null,'False','false']){
   timers=[];let calls=0;
   const headers={'x-agentcc-request-id':ID};if(dispatched!==null)headers['x-agentcc-dispatched']=dispatched;
   const client=new api.AgentCC({apiKey:'offline-fixture',baseUrl:'https://gateway.test',maxRetries:2,...settings,fetch:async()=>{calls++;return new Response(JSON.stringify({error:{code}}),{status:503,headers});}});
   let error;try{await client[method](request);}catch(e){error=e;}
   rows.push({method,per_error_retry_policy:perError,code,dispatched_header:dispatched,attempts:calls,error_class:error.name,evidence:error.gatewayEvidence,guidance:error.remedy??null,retry_sleeps:timers.length,explicit_contract_precedence:code==='managed_billing_unavailable'});
  }
 }
 return rows;
}


async function bodyGuidanceEvidence(api) {
 const rows=[];
 for(const method of ['request','requestWithResponse','requestStream']) for(const status of [200,246]) for(const dispatch of [null,'False']) {
  let attempts=0; const callbacks=[];
  const headers={'x-agentcc-request-id':ID};if(dispatch!==null)headers['x-agentcc-dispatched']=dispatch;
  const observer=new class extends api.CallbackHandler {onError(_request,error){callbacks.push(error);}};
  const client=new api.AgentCC({apiKey:'offline-fixture',baseUrl:'https://gateway.test',maxRetries:3,callbacks:[observer],fetch:async()=>{attempts++;return new Response(new ReadableStream({start(c){c.error(new Error('synthetic body failure'));}}),{status,headers});}});
  let error;
  try {if(method==='requestStream'){for await(const chunk of new api.Stream(await client.requestStream(request))) {}}else await client[method](request);}catch(e){error=e;}
  assert.ok(error instanceof (method==='requestStream'?api.StreamError:api.ResponseBodyError));assert.equal(attempts,1);
  rows.push({method,status,dispatch,attempts,error_class:error.name,message:error.message,remedy:error.remedy??null,evidence:error.gatewayEvidence,callback_same_error:method==='requestStream'?null:callbacks[0]===error});
 }
 return rows;
}

(async()=>{
 const cjs=require(BUILD+'/cjs/index.js');
 const cjsPolicy=require(BUILD+'/cjs/refusal-policy.js');
 const esm=await import(pathToFileURL(BUILD+'/esm/index.js').href);
 const esmPolicy=await import(pathToFileURL(BUILD+'/esm/refusal-policy.js').href);
 const c=await generate(cjs,cjsPolicy);
 const e=await generate(esm,esmPolicy);
 assert.deepEqual(c,e);
 const differences=[...diffRows('rows',c.rows,py.rows),...diffRows('variant_evidence',c.variant_evidence,py.variant_evidence)];
 for(const section of ['fallback_evidence','dispatch_wire_evidence','retry_after_evidence']) assert.deepEqual(c[section],py[section]);
 const exceptional=[
  ...differences.filter(d=>d.field==='stream_attempts'),
  {field:'maximum_automatic_retry_after_seconds',typescript:cjs.MAX_RETRY_AFTER_SECONDS,python:2147483647,justification:'Node/browser signed 32-bit millisecond timers versus the Python r6 seconds bound. Larger positive hints stop automatic replay instead of truncating the wait.',evidence:c.timer_boundary_evidence},
  {field:'successful_metadata_request_id_alias',typescript:'requestId is the validated ULID or null',python:py.header_evidence.legacy_success_metadata,justification:'Known Python r6 defect, not an approved compatibility exception: the pinned Python review requires its alias to be fixed. TypeScript alias regressions pass before and after this change. This comparison deliberately targets the pinned r6 table, not the concurrent Python fix.'},
  postHeaderBodyFailureDifference
 ];
 const parity={schema:'sdk/onekey-refusal-parity/v1',id:'gateway-refusal-parity',recorded_at:new Date().toISOString(),consumer:'TypeScript @future-agi/sdk/gateway',classification_key:py.classification_key,source:{commit:build.head_sha,tree:build.tree_sha,generator_sha256:hash(fs.readFileSync(__filename)),parity_labels_sha256:hash(fs.readFileSync(LABELS)),build_manifest_sha256:hash(fs.readFileSync(OUT+'/build-manifest.json'))},python_fixture_input:{sha256:PY_SHA,origin_table_sha256:'7b454b92e5ccf512911cc35e82bc8ae349f76687a87c26848018465a764b7e00',qualification:'Synthetic fixture data from the pinned Python r6 table; no Python source uploaded or runtime executed. Body guidance follows the supplied shared rule.'},current_contract_rows:py.current_contract_rows,...c,...rules,unknown_dispatch_evidence:await dispatchEvidence(cjs),unknown_body_guidance_evidence:await bodyGuidanceEvidence(cjs),methodology:{fixture_inputs:['http_status','code','condition','metadata_fields','metadata_presence','contract_retry','evaluated_metadata'],cjs_esm_runtime_equal:true,python_runtime_executed:false,network:'Infrastructure egress blocked; injected fetch only; recording fake timers.',explanation:'Adapted the verified previous generator for fresh CJS/ESM builds. All 58 rows and 25 variants are freshly observed on all four entrypoints; field-by-field comparison retains the explicitly enumerated language differences.'},documented_language_differences:exceptional,contract_precedence:'Recognized status/code rows keep their explicit retry rules even if dispatch is unknown or true. managed_billing_unavailable is an exercised contrast, not an unreported exception.',pending:[{scope:'aggregate root SDK build, npm tarball, published 0.7.0 differential, Python runtime, live services, billing settlement',status:'NOT_CERTIFIED',reason:'This proof covers the gateway-client Node 22 CI job, fresh dual builds and offline head/base behavior only.'}]};
 assert.deepEqual(parity.unknown_dispatch_evidence,await dispatchEvidence(esm));
 assert.deepEqual(parity.unknown_body_guidance_evidence,await bodyGuidanceEvidence(esm));
 const comparison={schema:'sdk/literal-parity-comparison/v1',recorded_at:new Date().toISOString(),status:'PASS_WITH_ENUMERATED_DIFFERENCES',head_sha:build.head_sha,python_input:{path:PY,sha256:PY_SHA},comparison:'Field-by-field structural JSON comparison of every row and variant; no semantic normalization before comparison.',all_shared_labels_and_metadata_fields_literal_equal:true,rows:c.rows.length,variants:c.variant_evidence.length,compared_row_fields:Object.keys(c.rows[0]),row_field_comparisons:c.rows.concat(c.variant_evidence).reduce((n,r)=>n+Object.keys(r).length,0),unlisted_differences:0,literal_differences:differences,documented_language_differences:exceptional,identical_auxiliary_sections:['fallback_evidence','dispatch_wire_evidence','retry_after_evidence'],cjs_esm_runtime_equal:true,python_runtime_executed:false};
 
 
 write('refusal-parity.json',parity);
 write('literal-comparison.json',comparison);
 console.log(JSON.stringify({rows:c.rows.length,variants:c.variant_evidence.length,literal_differences:differences.length,stream_row_differences:differences.filter(d=>d.section==='rows'&&d.field==='stream_attempts').length,cjs_esm_equal:true,head:build.head_sha}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>{globalThis.setTimeout=originalTimer;Math.random=originalRandom;});
