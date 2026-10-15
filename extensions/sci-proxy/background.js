import { TOKEN } from './local-token.js';
import {loadRoutes, saveRoutes, website, proxyConfiguration} from './core/routes-网站规则-v17.js';

async function api(path, data = {}) {
  const response = await fetch(`http://127.0.0.1:17896${path}`, {
    method: 'POST', headers: {'Content-Type': 'application/json', 'X-Bridge-Token': TOKEN},
    body: JSON.stringify(data), signal: AbortSignal.timeout(30000)
  });
  if (!response.ok) throw new Error('本地管理服务认证失败');
  const result = await response.json();
  if (!result.ok) throw new Error(result.error);
  return result.data;
}

async function browserProxy(enabled) {
  const current = await chrome.proxy.settings.get({incognito: false});
  if (!['controllable_by_this_extension', 'controlled_by_this_extension'].includes(current.levelOfControl)) {
    throw new Error('代理由其他扩展或策略控制，请先停用冲突的代理扩展');
  }
  await chrome.proxy.settings.set({scope: 'regular', value: proxyConfiguration(enabled, await loadRoutes())});
  await chrome.privacy.network.webRTCIPHandlingPolicy.set({value: enabled ? 'disable_non_proxied_udp' : 'default'});
}

async function sync() {
  const state = await api('/status');
  await browserProxy(state.enabled);
  return state;
}
chrome.runtime.onInstalled.addListener(() => sync().catch(() => {}));
chrome.runtime.onStartup.addListener(() => sync().catch(() => {}));
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  (async () => {
    if (sender.id !== chrome.runtime.id) throw new Error('无效来源');
    let data;
    if (message.action === 'site-status') {
      const tab = await chrome.tabs.get(message.data.tabId);
      const host = website(tab.pendingUrl || tab.url);
      const routes = await loadRoutes();
      data = {host, mode: routes[host] || 'proxy', remembered: Object.hasOwn(routes, host)};
    } else if (message.action === 'site-mode') {
      const tab = await chrome.tabs.get(message.data.tabId);
      const host = website(tab.pendingUrl || tab.url);
      if (host !== message.data.host) throw new Error('页面已经变化，请重新打开面板。');
      if (!['proxy', 'direct'].includes(message.data.mode)) throw new Error('不支持的连接方式。');
      const routes = await loadRoutes();
      const previous = {...routes};
      const service = await api('/status');
      if (message.data.mode === 'proxy' && !service.enabled) await api('/enabled', {enabled:true});
      routes[host] = message.data.mode;
      await saveRoutes(routes);
      try { await browserProxy(message.data.mode === 'proxy' || service.enabled); }
      catch(error) { await saveRoutes(previous); throw error; }
      data = {host, mode:message.data.mode, remembered:true};
    } else if (message.action === 'status') data = await sync();
    else if (message.action === 'apply') data = await api('/apply', message.data);
    else if (message.action === 'enabled') {
      if (message.data.enabled) { data = await api('/enabled', message.data); await browserProxy(true); }
      else { await browserProxy(false); data = await api('/enabled', message.data); }
    } else if (message.action === 'test') data = await api('/test');
    else throw new Error('无效操作');
    reply({ok: true, data});
  })().catch(error => reply({ok: false, error: error.message.includes('fetch') ? '本地服务未启动，请使用专用启动入口' : error.message}));
  return true;
});
