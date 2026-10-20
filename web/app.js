'use strict';
const $ = id => document.getElementById(id);
let state = {request:null,result:null}, busy = false, view = 'preview', drawSerial = 0;
const percent = n => `${(n*100).toFixed(1)}%`;
const text = (id,value) => { $(id).textContent=value; };
function message(value){text('status',value);}
function fail(error){$('error').hidden=false;text('error',error.message || String(error));}
function resetError(){ $('error').hidden=true; }
function ready(){
  $('analyze').disabled=busy || !state.request?.reference || !state.request?.captures?.length || !$('planar').checked;
  $('recapture').disabled=busy || state.request?.evidence_kind!=='synthetic_fixture' || state.request.captures.length>=6 || state.request.captures.some(x=>x.name==='bridge.png');
  for(const id of ['report','preview','bundle'])$(id).disabled=busy || !state.result;
  $('save').disabled=busy || !state.request;
  for(const id of ['sample','invalid','reference','captures','width','height','planar','clear'])$(id).disabled=busy;
  $('files').querySelectorAll('button').forEach(b=>b.disabled=busy);
}
function invalidate(){state.result=null;render();}
function requestFields(){
  if(!state.request)return;
  Object.assign(state.request,{width_mm:Number($('width').value),height_mm:Number($('height').value),planar_surface_confirmed:$('planar').checked,cell_px:64});
}
function files(){
  const list=$('files');list.replaceChildren();
  if(!state.request)return;
  if(state.request.reference){const li=document.createElement('li');li.textContent=`Overview: ${state.request.reference.name}`;list.append(li);}
  state.request.captures.forEach((file,index)=>{
    const li=document.createElement('li'),name=document.createElement('span'),button=document.createElement('button');
    name.textContent=file.name;button.textContent='Remove';button.setAttribute('aria-label',`Remove ${file.name}`);
    button.onclick=()=>{state.request.captures.splice(index,1);invalidate();};li.append(name,button);list.append(li);
  });
}
function render(){
  files();ready();
  text('kind',!state.request?'No capture set loaded.':state.request.evidence_kind==='synthetic_fixture'?'SYNTHETIC DEMO · Original generated board. Not camera validation.':'YOUR PHOTOGRAPHS · Planarity and reference preparation are operator declarations.');
  const report=state.result?.report;
  $('empty').hidden=Boolean(report);
  text('coverage',report?percent(report.summary.coverage_fraction):'—');
  text('quality',report?percent(report.summary.quality_coverage_fraction):'—');
  text('cells',report?`${report.summary.supported_cells} / ${report.summary.total_cells}`:'—');
  $('sources').replaceChildren();
  if(!report){
    text('decision','Inspect a set to find the gap.');text('target','The overview aligns your photographs; it cannot fill a missing region.');
    text('execution','Runtime evidence is recorded after analysis.');draw();return;
  }
  const region=report.largest_deficient_region;
  text('decision',region?'Recapture the highlighted region.':'Controlled quality thresholds met.');
  text('target',region?`Aim near (${region.target_center_mm.join(', ')}) mm from the top-left. The deficient region spans [${region.bounds_mm.join(', ')}] mm. Include overlap into registered detail.`:`${report.summary.supported_cells} of ${report.summary.total_cells} cells meet the fixed thresholds. Source coverage is ${percent(report.summary.coverage_fraction)}, not a guarantee of every pixel or archival fitness.`);
  text('execution',`OpenCV ${report.runtime.opencv} · ${report.execution.location==='aws-lambda'?'AWS Lambda execution':'LOCAL computation — AWS not verified'} · ${report.processing_seconds}s · ${report.summary.registered} registered / ${report.summary.rejected} rejected · ${report.evidence_kind==='synthetic_fixture'?'synthetic fixture':'operator-declared camera captures'}`);
  report.sources.forEach(source=>{
    const li=document.createElement('li'),title=document.createElement('strong'),detail=document.createElement('span'),hash=document.createElement('small');
    title.textContent=`${source.original_name || source.id} · ${source.status==='registered'?'Registered':'Unable to register'}`;
    detail.textContent=source.status==='registered'?`${source.inliers} inliers · reprojection error ${source.reprojection_rmse_px}px`:`Contributes zero coverage · ${source.reason.replaceAll('_',' ')}`;
    hash.textContent=`SHA-256 ${source.sha256}`;li.append(title,detail,hash);$('sources').append(li);
  });draw();
}
async function draw(){
  const serial=++drawSerial,canvas=$('map'),ctx=canvas.getContext('2d'),report=state.result?.report;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if(!report)return;
  const image=new Image();image.src=`data:image/png;base64,${state.result.artifacts[view].base64}`;
  try{await image.decode();}catch{return;}
  if(serial!==drawSerial)return;
  canvas.width=report.reference.width_px;canvas.height=report.reference.height_px;
  ctx.drawImage(image,0,0);ctx.lineWidth=Math.max(2,canvas.width/350);
  for(const cell of report.cells.filter(c=>c.status!=='supported')){
    const [x0,y0,x1,y1]=cell.bounds_px;ctx.fillStyle='rgba(185,88,41,.20)';ctx.strokeStyle='#f2a15b';
    ctx.fillRect(x0,y0,x1-x0,y1-y0);ctx.strokeRect(x0,y0,x1-x0,y1-y0);
  }
  canvas.setAttribute('aria-label',`${percent(report.summary.coverage_fraction)} source coverage; ${report.summary.supported_cells} of ${report.summary.total_cells} cells meet quality thresholds.`);
}
async function api(path,options){
  const response=await fetch(path,{...options,signal:AbortSignal.timeout(65000)});
  let data;try{data=await response.json();}catch{throw new Error(`The worker returned HTTP ${response.status}. Try again shortly.`);}
  if(!response.ok)throw new Error(data.error?.message || `HTTP ${response.status}`);
  return data;
}
async function work(action){
  if(busy)return;busy=true;resetError();ready();
  try{await action();}catch(error){fail(error);message('Inspection not completed. Your inputs are still available.');}
  finally{busy=false;ready();}
}
async function loadSample(scenario){
  await work(async()=>{
    message('Loading the owned synthetic capture set…');
    const sample=await api(`/api/sample?scenario=${scenario}`);
    state={request:sample.request,result:null};$('width').value=state.request.width_mm;$('height').value=state.request.height_mm;$('planar').checked=true;
    $('reference').value='';$('captures').value='';render();message('Synthetic inputs loaded. Inspect coverage to run the real vision pipeline.');
  });
}
$('sample').onclick=()=>loadSample('gap');
$('invalid').onclick=()=>loadSample('invalid');
$('recapture').onclick=()=>work(async()=>{
  const sample=await api('/api/sample?scenario=recaptured');
  if(state.request.reference.base64!==sample.request.reference.base64)throw new Error('Sample recapture does not match this overview.');
  const bridge=sample.request.captures.find(x=>x.name==='bridge.png');
  state.request.captures.push(bridge);invalidate();message('Bridge photograph added. Inspect again to measure the change.');
});
$('analyze').onclick=()=>work(async()=>{
  requestFields();message('Registering sources and measuring coverage…');
  const result=await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.request)});
  state.result=result;render();message('Inspection complete. Results correspond to the current capture set.');
});
async function upload(file){
  if(file.size>1500000)throw new Error(`${file.name} exceeds 1.5 MB. Export a smaller image before uploading.`);
  const buffer=await file.arrayBuffer();let binary='';const bytes=new Uint8Array(buffer);
  for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  return {name:file.name,base64:btoa(binary)};
}
function cameraState(){
  if(!state.request || state.request.evidence_kind!=='camera_capture'){
    state={request:{reference:null,captures:[],width_mm:Number($('width').value),height_mm:Number($('height').value),cell_px:64,evidence_kind:'camera_capture',planar_surface_confirmed:false},result:null};
    $('planar').checked=false;
  }
}
$('reference').onchange=()=>work(async()=>{
  const file=$('reference').files[0];if(!file)return;
  const image=await upload(file);cameraState();state.request.reference=image;invalidate();
  message('Overview selected. Add overlapping details and confirm the geometry.');
});
$('captures').onchange=()=>work(async()=>{
  const selected=Array.from($('captures').files);if(!selected.length)return;
  const current=state.request?.evidence_kind==='camera_capture'?state.request.captures.length:0;
  if(current+selected.length>6)throw new Error('At most six detail photographs are supported.');
  const images=await Promise.all(selected.map(upload));cameraState();state.request.captures.push(...images);$('captures').value='';invalidate();
  message('Detail photographs added. Inspect the current set.');
});
for(const id of ['width','height','planar'])$(id).onchange=()=>{requestFields();invalidate();};
document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{
  view=button.dataset.view;document.querySelectorAll('[data-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===button)));draw();
});
function download(name,value,type='application/json'){
  const blob=value instanceof Blob?value:new Blob([JSON.stringify(value,null,2)],{type}),url=URL.createObjectURL(blob);
  const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('report').onclick=()=>download('surfaceledger-report.json',state.result.report);
$('bundle').onclick=()=>download('surfaceledger-capture-set.json',{format:'surfaceledger-browser-export-v1',...state});
$('preview').onclick=()=>{
  const raw=atob(state.result.artifacts.preview.base64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
  download('surfaceledger-source-preview.png',new Blob([bytes],{type:'image/png'}));
};
async function database(){
  return new Promise((resolve,reject)=>{
    const request=indexedDB.open('surfaceledger-local',1);
    request.onupgradeneeded=()=>request.result.createObjectStore('project');
    request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
  });
}
async function stored(mode,value){
  const db=await database();
  try{return await new Promise((resolve,reject)=>{
    const tx=db.transaction('project',mode==='load'?'readonly':'readwrite'),store=tx.objectStore('project');
    const request=mode==='load'?store.get('current'):mode==='save'?store.put(value,'current'):store.delete('current');
    tx.oncomplete=()=>resolve(request.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error || new Error('Local storage was interrupted.'));
  });}finally{db.close();}
}
$('save').onclick=()=>work(async()=>{requestFields();await stored('save',state);text('saved','Saved on this device. Reload restores inputs and the measured report.');});
$('clear').onclick=()=>work(async()=>{
  await stored('clear');state={request:null,result:null};$('reference').value='';$('captures').value='';$('planar').checked=false;
  text('saved','Local capture set and report deleted.');render();message('Cleared. No server copy is retained.');
});
async function boot(){
  render();
  try{const health=await api('/api/health');text('runtime',`OpenCV ${health.runtime.opencv} · ${health.execution.location==='aws-lambda'?'AWS Lambda':'local worker'}`);}
  catch{ text('runtime','Vision worker unavailable');}
  try{
    const restored=await stored('load');
    if(restored?.request){state=restored;$('width').value=state.request.width_mm;$('height').value=state.request.height_mm;$('planar').checked=state.request.planar_surface_confirmed;render();text('saved','Restored from this device. The report retains its original execution evidence.');message('Saved capture set restored.');}
  }catch{ text('saved','Local saving is unavailable in this browser. Downloads still work.');}
}
boot();
