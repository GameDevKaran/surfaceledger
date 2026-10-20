import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
const origin='http://127.0.0.1:8785';
const record={at:new Date().toISOString(),scope:'local Linux Lambda runtime emulator; NOT AWS execution',passed:false,checks:[]};
async function invoke(method,path,payload,headers={}){
  const [rawPath,rawQueryString='']=path.split('?');
  const response=await fetch(origin+'/2015-03-31/functions/function/invocations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    version:'2.0',rawPath,rawQueryString,headers:{origin,'content-type':'application/json',...headers},
    requestContext:{http:{method,path:rawPath,sourceIp:'127.0.0.1'}},
    body:payload?JSON.stringify(payload):'',isBase64Encoded:false
  }),signal:AbortSignal.timeout(65000)});
  assert.equal(response.status,200);return response.json();
}
try{
  const health=await invoke('GET','/api/health');assert.equal(health.statusCode,200);
  const runtime=JSON.parse(health.body);assert.equal(runtime.runtime.opencv,'5.0.0');
  assert.equal(runtime.execution.source_commit,process.env.EXPECTED_SOURCE_COMMIT);
  record.runtime=runtime;record.checks.push('Pinned OpenCV5 and exact source commit execute in Lambda Linux base');
  const ui=await invoke('GET','/');assert.equal(ui.statusCode,200);assert.match(ui.body,/SurfaceLedger/);
  record.checks.push('Packaged static interface served by actual handler');
  const supplied=JSON.parse((await invoke('GET','/api/sample?scenario=gap')).body);
  const analyzed=await invoke('POST','/api/analyze',supplied.request);assert.equal(analyzed.statusCode,200,analyzed.body);
  const result=JSON.parse(analyzed.body);
  assert.deepEqual(result.report.largest_deficient_region.bounds_px,[320,0,448,512]);
  assert.equal(result.report.summary.registered,2);
  assert.equal(result.report.execution.aws_verified,false,'Local emulator must not claim real AWS verification');
  record.analysis={runtime:result.report.runtime,summary:result.report.summary,execution:result.report.execution,processing_seconds:result.report.processing_seconds};
  record.checks.push('Actual Linux subprocess OpenCV analysis under1GB/0.6CPU/read-only root');
  const denied=await invoke('POST','/api/analyze',{}, {origin:'https://untrusted.invalid'});
  assert.equal(denied.statusCode,403);record.checks.push('Foreign origin rejected');
  record.passed=true;
}catch(error){record.error=String(error);process.exitCode=1;}
finally{mkdirSync('.local/container',{recursive:true});writeFileSync('.local/container/verification.json',JSON.stringify(record,null,2)+'\n');console.log(JSON.stringify(record,null,2));}
