import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {chromium,expect} from '@playwright/test';

const external = process.env.SURFACELEDGER_VERIFY_URL;
const url=external || 'http://127.0.0.1:8784';
if(external && !/^https:\/\/[a-z0-9]+\.lambda-url\.us-east-1\.on\.aws\/?$/.test(external))
  throw new Error('Live verification must target the exact authorized SurfaceLedger Lambda URL.');
const folder=external?'.local/live-browser':'.local/browser';mkdirSync(folder,{recursive:true});
const report={at:new Date().toISOString(),url,scope:external?'deployed HTTPS':'local HTTP',checks:[],passed:false};
let server,browser;
try{
  if(!external){
    const python=process.env.SURFACELEDGER_PYTHON || (process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
    server=spawn(python,['-m','surfaceledger.web','--port','8784'],{stdio:['ignore','pipe','pipe'],shell:false});
    let error='';server.stderr.on('data',x=>{error+=x;});
    for(let n=0;;n++){
      if(server.exitCode!==null)throw new Error(`Local server exited: ${error}`);
      try{if((await fetch(url+'/api/health')).ok)break;}catch{}
      if(n>60)throw new Error('Local server did not start.');
      await new Promise(r=>setTimeout(r,250));
    }
  }
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1100},recordVideo:{dir:folder+'/video'}});
  const page=await context.newPage(), errors=[];
  page.on('pageerror',x=>errors.push(x.message));
  const responses=[];
  page.on('response',async response=>{
    if(response.url().endsWith('/api/analyze') && response.ok())responses.push(await response.json());
  });
  await page.goto(url);await expect(page.locator('#runtime')).toContainText('OpenCV 5');
  await page.getByRole('button',{name:'Load sample gap',exact:true}).click();
  await expect(page.locator('#kind')).toContainText('SYNTHETIC DEMO');
  await expect(page.getByRole('button',{name:'Inspect coverage'})).toBeEnabled();
  await page.getByRole('button',{name:'Inspect coverage'}).click();
  await expect(page.locator('#status')).toContainText('Inspection complete',{timeout:65000});
  await expect(page.locator('#coverage')).toHaveText('82.5%');
  await expect(page.locator('#target')).toContainText('[320, 0, 448, 512]');
  await expect(page.locator('#execution')).toContainText(external?'AWS Lambda execution':'LOCAL computation');
  await page.screenshot({path:folder+'/surfaceledger-gap.png',fullPage:true});
  report.checks.push('Real OpenCV HTTP analysis finds authored synthetic gap; execution location correctly labeled');
  await page.getByRole('button',{name:'Add sample recapture',exact:true}).click();
  await expect(page.locator('#status')).toContainText('Bridge photograph added');
  await page.getByRole('button',{name:'Inspect coverage'}).click();
  await expect(page.locator('#status')).toContainText('Inspection complete',{timeout:65000});
  await expect(page.locator('#coverage')).toHaveText('99.4%');
  await expect(page.locator('#cells')).toHaveText('96 / 96');
  await expect(page.locator('#decision')).toHaveText('Controlled quality thresholds met.');
  report.checks.push('Added recapture reruns real pipeline;96 cells pass without claiming100% pixels');
  await page.getByRole('button',{name:'Save on this device',exact:true}).click();
  await expect(page.locator('#saved')).toContainText('Saved on this device');
  await page.reload();await expect(page.locator('#status')).toContainText('Saved capture set restored');
  await expect(page.locator('#cells')).toHaveText('96 / 96');
  report.checks.push('IndexedDB preserves capture inputs and measured report across reload');
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download report',exact:true}).click();
  const exported=await download;await exported.saveAs(folder+'/exported-report.json');
  const parsed=JSON.parse(readFileSync(folder+'/exported-report.json','utf8'));
  assert.equal(parsed.summary.supported_cells,96);assert.equal(parsed.execution.location,external?'aws-lambda':'local');
  assert.equal(parsed.runtime.opencv.split('.')[0],'5');
  report.checks.push('Downloaded report contains genuine runtime and source provenance');
  await page.screenshot({path:folder+'/surfaceledger-recaptured.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile horizontal overflow');
  await page.screenshot({path:folder+'/surfaceledger-mobile.png',fullPage:true});
  report.checks.push('Mobile390px layout fits viewport');
  await page.getByRole('button',{name:'Try rejected capture',exact:true}).click();
  await expect(page.locator('#status')).toContainText('Synthetic inputs loaded');
  await page.getByRole('button',{name:'Inspect coverage'}).click();
  await expect(page.locator('#status')).toContainText('Inspection complete',{timeout:65000});
  await expect(page.locator('#coverage')).toHaveText('0.0%');
  await expect(page.locator('#sources')).toContainText('Unable to register');
  report.checks.push('Blank capture rejected and contributes zero coverage');
  await page.getByRole('button',{name:'Clear this device',exact:true}).click();
  await expect(page.locator('#saved')).toContainText('deleted');
  await page.reload();await expect(page.locator('#runtime')).toContainText('OpenCV 5');
  await expect(page.locator('#kind')).toHaveText('No capture set loaded.');
  await expect(page.locator('#coverage')).toHaveText('—');
  report.checks.push('Explicit deletion survives reload');
  // Exercise the actual file inputs with owned synthetic PNGs. This is upload
  // plumbing evidence, never evidence of physical camera capture or accuracy.
  const fixture=await (await fetch(url+'/api/sample?scenario=gap')).json();
  await page.locator('#reference').setInputFiles({name:'synthetic-upload-overview.png',mimeType:'image/png',buffer:Buffer.from(fixture.request.reference.base64,'base64')});
  await expect(page.locator('#files')).toContainText('synthetic-upload-overview.png');
  await page.locator('#captures').setInputFiles(fixture.request.captures.map(x=>({name:`synthetic-upload-${x.name}`,mimeType:'image/png',buffer:Buffer.from(x.base64,'base64')})));
  await expect(page.locator('#files')).toContainText('synthetic-upload-right.png');
  await page.locator('#planar').check();
  await page.getByRole('button',{name:'Inspect coverage'}).click();
  await expect(page.locator('#status')).toContainText('Inspection complete',{timeout:65000});
  await expect(page.locator('#coverage')).toHaveText('82.5%');
  report.checks.push('File-picker upload path executes real analysis on explicitly synthetic test images; not camera validation');
  const isolated=await browser.newContext();const clean=await isolated.newPage();await clean.goto(url);
  await expect(clean.locator('#kind')).toHaveText('No capture set loaded.');await isolated.close();
  report.checks.push('Independent browser has no user inputs or report');
  assert.deepEqual(errors,[]);assert.equal(responses.length,4);
  report.analysis=responses.map(x=>({runId:x.runId,summary:x.report.summary,runtime:x.report.runtime,execution:x.report.execution}));
  report.passed=true;await context.close();
}catch(error){report.error=String(error);process.exitCode=1;}
finally{
  await browser?.close();server?.kill();writeFileSync(folder+'/verification.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}
