import capture from '../core/environment-环境采集-v2.js';
import {compareSnapshot} from '../core/compare-环境比较-v2.js';
import {snapshot,mask} from '../core/snapshot-快照-v1.js';
const $=id=>document.getElementById(id);
let baseline=null;
let current=null, timer=null, busy=false, tab=null, storeId=null;
function status(text,error=false){$('status').textContent=text;$('status').className=error?'error':'';}
function clear(){$('environment').textContent='';current=null;$('export').disabled=true;$('list').replaceChildren();}
function render(){
  $('list').replaceChildren();
  for(const c of current?.cookies||[]){
    const card=document.createElement('article');card.className='cookie';
    const name=document.createElement('strong');name.textContent=c.name;
    const value=document.createElement('code');value.textContent=$('reveal').checked?c.value:mask(c.value);
    const meta=document.createElement('div');meta.className='meta';
    meta.textContent=`${c.domain}${c.path} · ${c.httpOnly?'HttpOnly · ':''}${c.secure?'Secure · ':''}${c.sameSite??'未指定 SameSite'}${c.partitionKey?' · 分区 Cookie':''}`;
    card.append(name,value,meta);$('list').append(card);
  }
}
async function read(){
  if(busy)return;
  busy=true;$('read').disabled=true;clear();
  try{
    const url=new URL($('url').value.trim());
    if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error('请输入有效的 HTTP 或 HTTPS 网页地址。');
    const details={url:url.href};if(storeId)details.storeId=storeId;
    const cookies=await chrome.cookies.getAll(details);
    current=snapshot(url.href,cookies);
    const live = tab?.id != null ? await chrome.tabs.get(tab.id) : null;
    if (live?.url && new URL(live.url).origin === url.origin) {
      const saved = await chrome.storage.local.get('environmentProfileId');
      const profileId = saved.environmentProfileId || crypto.randomUUID();
      if (!saved.environmentProfileId) await chrome.storage.local.set({environmentProfileId:profileId});
      const rule = {origin:url.origin, profileId,
        authenticatedSelector:$('authenticated').value.trim(), unauthenticatedSelector:$('unauthenticated').value.trim()};
      const results = await chrome.scripting.executeScript({target:{tabId:tab.id},func:capture,args:[rule]});
      const info = results[0]?.result;
      if (!info?.environment) throw Error('Environment capture failed');
      const after = await chrome.tabs.get(tab.id);
      if (after.url !== live.url) throw Error('Page changed; read again');
      Object.assign(current,info);
      await chrome.storage.local.set({['loginRule:'+url.origin]:rule});
    } else {
      current.loginEvidence = {status:'unknown',method:'page_unavailable'};
    }
    showEnvironment();render();$('export').disabled=false;
    status(`已读取 ${cookies.length} 条 Cookie · ${new Date().toLocaleTimeString()}${cookies.length?'':' · 可先访问或登录目标网站再刷新'}`);
  }catch(e){clear();status(e.message,true);}finally{busy=false;$('read').disabled=false;}
}
$('read').onclick=read;
$('reveal').onchange=render;
$('url').oninput=()=>{clear();$('watch').checked=false;clearInterval(timer);timer=null;};
$('watch').onchange=()=>{clearInterval(timer);timer=null;if($('watch').checked){read();timer=setInterval(read,5000);}};
$('export').onclick=async()=>{
  if(!current)return;
  const saved=current;
  const blob=new Blob([JSON.stringify(saved,null,2)+'\n'],{type:'application/json'});
  const link=URL.createObjectURL(blob);
  try{
    const host=new URL(saved.sourceUrl).hostname.replace(/[^a-z0-9.-]/gi,'_');
    await chrome.downloads.download({url:link,filename:`cookies/${host}-${Date.now()}.json`,saveAs:true});
    status('已发起本地 JSON 导出。');
  }catch(e){status(e.message,true);}finally{setTimeout(()=>URL.revokeObjectURL(link),60000);}
};
window.addEventListener('pagehide',()=>clearInterval(timer));
(async()=>{
  try{
    [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(tab?.url&&/^https?:/.test(tab.url))$('url').value=tab.url;
    if(tab?.id!=null){const stores=await chrome.cookies.getAllCookieStores();storeId=stores.find(s=>s.tabIds.includes(tab.id))?.id??null;}
  }catch(e){status(e.message,true);}
})();

function showEnvironment() {
  const labels = {authenticated:'检测到已登录页面信号',unauthenticated:'检测到未登录页面信号',unknown:'登录状态未知'};
  const lines = [labels[current?.loginEvidence?.status] || labels.unknown];
  if (current?.environment) lines.push(`环境 ${current.fingerprint?.slice(0,12) || '摘要不可用'} · ${current.environment.timezone} · ${current.environment.languages.join(', ')}`);
  else lines.push('未采集环境：请在目标网页打开扩展。');
  if (baseline) lines.push(compareSnapshot(baseline,current).reason);
  $('environment').textContent=lines.join('\n');
}
$('baseline').onchange=async()=>{
  try {
    const file=$('baseline').files[0];if(!file)return;
    if(file.size>10*1024*1024)throw Error('快照文件超过 10 MB');
    baseline=JSON.parse(await file.text());
    if(!baseline || typeof baseline!=='object')throw Error('快照格式错误');
    showEnvironment();
  }catch(error){baseline=null;status(error.message,true);}
};
(async()=>{
  const [active]=await chrome.tabs.query({active:true,currentWindow:true});
  if(!active?.url || !/^https?:/.test(active.url))return;
  const key='loginRule:'+new URL(active.url).origin;
  const saved=await chrome.storage.local.get(key);
  if(saved[key]){$('authenticated').value=saved[key].authenticatedSelector||'';$('unauthenticated').value=saved[key].unauthenticatedSelector||'';}
})().catch(()=>{});
