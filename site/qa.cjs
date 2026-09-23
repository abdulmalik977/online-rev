// Local application QA through an isolated Chrome started for this task.
const fs=require('fs'); const {once}=require('events');
(async()=>{
 const origin=process.env.TASK007_QA_URL||'http://127.0.0.1:8777';
 const debug=process.env.TASK007_QA_DEBUG||'http://127.0.0.1:9227';
 const output=process.env.TASK007_QA_OUTPUT||'.runtime/task007-qa';
 fs.mkdirSync(output,{recursive:true});
 const tabs=await(await fetch(debug+'/json')).json();
 const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl); await once(ws,'open');
 let seq=0; const pending=new Map();
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}});
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 await send('Page.enable'); const results=[];
 for(const width of [320,390,430,1440]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:850,deviceScaleFactor:1,mobile:width<760});
  for(const page of ['index.html','privacy.html','unsubscribe.html']){
   await send('Page.navigate',{url:origin+'/'+page});
   let info;
   for(let i=0;i<40;i++){
    const r=await send('Runtime.evaluate',{expression:`JSON.stringify({ready:document.readyState,path:location.pathname,width:innerWidth,scroll:document.documentElement.scrollWidth,checkout:document.querySelector('.price-card button')?.disabled,heading:document.querySelector('h1')?.textContent,load_ms:performance.getEntriesByType('navigation')[0]?.loadEventEnd,cookies:document.cookie,concept:document.querySelector('.concept-request a')?.getAttribute('href'),conceptText:document.querySelector('.concept-request')?.textContent,forms:document.querySelectorAll('form').length})`,returnByValue:true});
    info=JSON.parse(r.result.value);
    if(info.ready==='complete'&&info.path.endsWith(page)&&info.load_ms>0)break;
    await new Promise(r=>setTimeout(r,50));
   }
   results.push({viewport:width,page,...info});
   if(page==='index.html'&&[390,1440].includes(width)){
    const {contentSize}=await send('Page.getLayoutMetrics');
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:contentSize.height,scale:1}});
    fs.writeFileSync(output+'/'+width+'.png',Buffer.from(shot.data,'base64'));
    if(width===390){
     const bounds=await send('Runtime.evaluate',{expression:'JSON.stringify((()=>{const r=document.querySelector(".price-card").getBoundingClientRect();return {y:r.top+scrollY,height:r.height};})())',returnByValue:true});
     const rect=JSON.parse(bounds.result.value);
     const card=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:Math.max(0,rect.y-10),width,height:rect.height+20,scale:1}});
     fs.writeFileSync(output+'/concept-card.png',Buffer.from(card.data,'base64'));
    }

   }
  }
 }
 fs.writeFileSync(output+'/layout.json',JSON.stringify(results,null,2));
 const failed=results.filter(x=>x.width!==x.viewport||x.scroll>x.width||!x.heading||x.cookies||x.page==='index.html'&&(!x.checkout||!x.concept?.startsWith('mailto:')||x.forms!==0));
 console.log(JSON.stringify({checks:results.length,failed,max_local_load_ms:Math.max(...results.map(x=>x.load_ms))},null,2));
 ws.close(); if(failed.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
