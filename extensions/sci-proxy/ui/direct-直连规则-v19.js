import {loadRoutes} from '../core/routes-网站规则-v17.js';

const root = document.getElementById('direct-rules');
let revision = 0;
async function refresh() {
  const current = ++revision;
  try {
    const [routes, settings] = await Promise.all([
      loadRoutes(), chrome.proxy.settings.get({incognito:false})
    ]);
    if (current !== revision) return;
    const hosts = Object.keys(routes).filter(host => routes[host] === 'direct').sort();
    root.replaceChildren();
    const title = document.createElement('h2');
    title.textContent = `已保存的直连规则（${hosts.length}）`;
    root.append(title);
    const status = document.createElement('p');
    status.textContent = settings.value.mode === 'direct'
      ? '当前为全局直连：所有网站直接连接，以下规则仍保留。'
      : settings.levelOfControl === 'controlled_by_this_extension' && settings.value.mode === 'pac_script'
        ? '当前按网站规则连接；以下域名使用直连。'
        : '当前代理未由 sci-proxy 网站规则控制，以下仅表示已保存的偏好。';
    root.append(status);
    if (hosts.length) {
      const list = document.createElement('ul');
      list.setAttribute('aria-label', '已保存的直连域名');
      for (const host of hosts) {
        const row = document.createElement('li');
        row.textContent = host;
        list.append(row);
      }
      root.append(list);
    } else {
      const empty = document.createElement('p');
      empty.textContent = '尚未保存任何网站直连规则。';
      root.append(empty);
    }
    const note = document.createElement('p');
    note.textContent = '网站规则精确匹配域名，不自动包含子域名。';
    const builtin = document.createElement('p');
    builtin.textContent = '内置本机直连：localhost、127.0.0.1、::1（IPv6）。';
    root.append(note, builtin);
  } catch {
    if (current === revision) root.textContent = '无法读取直连规则，请重新打开页面。';
  }
}
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.siteRoutesV1) refresh();
});
chrome.proxy.settings.onChange.addListener(refresh);
refresh();
