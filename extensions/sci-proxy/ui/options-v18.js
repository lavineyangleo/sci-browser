const $ = id => document.getElementById(id);
const fields = ['host', 'port', 'username', 'password'];
let ready = false;
function message(text, error = false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; }
async function request(action, data) {
  const result = await chrome.runtime.sendMessage({action, data});
  if (!result?.ok) throw new Error(result?.error || '扩展后台没有响应');
  return result.data;
}
async function busy(task) {
  document.querySelectorAll('button,#enabled').forEach(e => e.disabled = true);
  try { await task(); } catch (error) { message(error.message, true); }
  finally { document.querySelectorAll('button,#enabled').forEach(e => e.disabled = false); $('enabled').disabled = !ready; }
}
function state(enabled, running = enabled) {
  $('enabled').checked = enabled;
  document.body.dataset.status = enabled && running ? 'enabled' : enabled ? 'error' : 'direct';
  $('state').textContent = enabled && running ? '代理已开启' : enabled ? '代理尚未就绪' : '直连模式';
  $('state-detail').textContent = enabled && running ? '浏览器流量通过当前节点连接' : enabled ? '请重新开启代理以恢复连接' : '浏览器直接连接网络';
}
$('import').onclick = () => {
  try {
    const url = new URL($('url').value.trim());
    if (!['socks5:', 'socks5h:'].includes(url.protocol) || !url.hostname || !url.port || url.search || url.hash || (url.pathname && url.pathname !== '/')) throw new Error('请输入完整有效的SOCKS5链接');
    $('host').value = url.hostname.replace(/^\[|\]$/g, ''); $('port').value = url.port;
    $('username').value = decodeURIComponent(url.username); $('password').value = decodeURIComponent(url.password);
    $('url').value = ''; message('已导入，保存后生效');
  } catch (error) { message(error.message, true); }
};
$('reveal').onchange = () => $('password').type = $('reveal').checked ? 'text' : 'password';
$('form').onsubmit = event => { event.preventDefault(); busy(async () => {
  const profile = Object.fromEntries(fields.map(k => [k, $(k).value])); profile.port = Number(profile.port);
  await request('apply', profile); $('result').hidden = true; message('配置已保存并应用');
}); };
$('enabled').onchange = () => { const enabled = $('enabled').checked; busy(async () => {
  try { await request('enabled', {enabled}); state(enabled); message(enabled ? '浏览器代理已开启' : '浏览器已切换直连'); }
  catch (error) { state(!enabled); throw error; }
}); };
$('test').onclick = () => busy(async () => {
  message('正在测试已保存的节点…'); $('result').hidden = true;
  const result = await request('test'); $('ip').textContent = result.ip;
  $('latency').textContent = `HTTPS ${result.status} · ${result.seconds.toFixed(2)} 秒`;
  $('result').hidden = false; message('出口验证成功，结果来自当前真实连接');
});
busy(async () => {
  try {
    const data = await request('status');
    fields.forEach(k => $(k).value = data.profile[k]);
    ready = true; state(data.enabled, data.running);
    if(data.enabled && !data.running) message('代理服务未运行，请重新开启代理', true);
  } catch(error) {
    document.body.dataset.status = 'error'; $('state').textContent = '服务未连接';
    $('state-detail').textContent = '请通过 sci-browser 启动器打开浏览器';
    throw error;
  }
});
