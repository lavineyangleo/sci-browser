const $ = id => document.getElementById(id);
let site = null, ready = false, enabled = false;
async function request(action, data) {
  const result = await chrome.runtime.sendMessage({action, data});
  if (!result?.ok) throw new Error(result?.error || '后台没有响应');
  return result.data;
}
function render() {
  $('direct').setAttribute('aria-pressed', String(!enabled));
  $('proxy').setAttribute('aria-pressed', String(enabled));
  $('status').textContent = enabled ? '代理已开启' : '直连';
  $('hint').textContent = enabled ? '按网站记住选择，刷新网页后生效。' : '当前全部直连，网站偏好仍然保留。';
}
async function run(task) {
  $('direct').disabled = $('proxy').disabled = $('route').disabled = true;
  $('message').textContent = '';
  try { await task(); } catch (error) { $('message').textContent = error.message; }
  finally {
    $('direct').disabled = $('proxy').disabled = !ready;
    $('route').disabled = !site || !ready;
  }
}
for (const mode of ['direct', 'proxy']) {
  $(mode).onclick = () => run(async () => {
    await request('enabled', {enabled: mode === 'proxy'});
    enabled = mode === 'proxy'; render();
  });
}
$('route').onchange = () => run(async () => {
  try {
    const value = await request('site-mode', {tabId:site.tabId, host:site.host, mode:$('route').value});
    site = {...site, ...value};
    if (value.mode === 'proxy') enabled = true;
    render(); $('hint').textContent = '已记住此网站的选择，刷新网页后生效。';
  } finally { $('route').value = site.mode; }
});
for (const id of ['options','server']) $(id).onclick = async () => {
  try { await chrome.runtime.openOptionsPage(); window.close(); }
  catch (error) { $('message').textContent = error.message; }
};
run(async () => {
  const state = await request('status');
  enabled = state.enabled; ready = true; render();
  if (enabled && !state.running) $('status').textContent = '代理未就绪';
  const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
  if (!tab?.id || !/^https?:/.test(tab.pendingUrl || tab.url || '')) return;
  site = {...await request('site-status', {tabId:tab.id}), tabId:tab.id};
  $('host').textContent = site.host; $('route').value = site.mode;
});
