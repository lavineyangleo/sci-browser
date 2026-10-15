import {snapshot,mask} from '../core/snapshot-快照-v1.js';
const $=id=>document.getElementById(id);
let current=null, timer=null, busy=false, tab=null, storeId=null;
function status(text,error=false){$('status').textContent=text;$('status').className=error?'error':'';}
function clear(){current=null;$('export').disabled=true;$('list').replaceChildren();}
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
    current=snapshot(url.href,cookies);render();$('export').disabled=false;
    status(`已读取 ${cookies.length} 条 Cookie · ${new Date().toLocaleTimeString()}${cookies.length?'':' · 可先访问或登录目标网站再刷新'}`);
  }catch(e){status(e.message,true);}finally{busy=false;$('read').disabled=false;}
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
