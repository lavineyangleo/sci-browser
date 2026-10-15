const STORAGE_KEY = 'siteRoutesV1';
export const MODES = ['proxy', 'direct'];

export function website(url) {
  const parsed = new URL(url);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('此页面不支持设置连接方式。');
  return parsed.hostname.toLowerCase();
}

export async function loadRoutes() {
  const stored = (await chrome.storage.local.get(STORAGE_KEY))[STORAGE_KEY];
  const routes = Object.create(null);
  if (stored && typeof stored === 'object') {
    for (const [host, mode] of Object.entries(stored)) {
      if (MODES.includes(mode)) routes[host] = mode;
    }
  }
  return routes;
}

export async function saveRoutes(routes) {
  await chrome.storage.local.set({[STORAGE_KEY]: routes});
}

export function proxyConfiguration(enabled, routes) {
  if (!enabled) return {mode: 'direct'};
  const direct = Object.keys(routes).filter(host => routes[host] === 'direct');
  return {mode: 'pac_script', pacScript: {mandatory: true, data: `
function FindProxyForURL(url, host) {
  host = host.toLowerCase();
  if (host === 'localhost' || host === '127.0.0.1' || host === '[::1]' || host === '::1') return 'DIRECT';
  var directHosts = ${JSON.stringify(direct)};
  if (directHosts.indexOf(host) !== -1) return 'DIRECT';
  return 'PROXY 127.0.0.1:17895';
}`}};
}
