export default async function capture(options = {}) {
  if (options.origin && location.origin !== options.origin) throw Error('页面已变化，请重新读取。');
  const environment = {
    version: 1,
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    languages: [...navigator.languages],
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen: {width: screen.width, height: screen.height, colorDepth: screen.colorDepth, pixelRatio: devicePixelRatio},
    hardwareConcurrency: navigator.hardwareConcurrency ?? null,
    deviceMemory: navigator.deviceMemory ?? null,
    maxTouchPoints: navigator.maxTouchPoints ?? null,
    userAgentData: navigator.userAgentData ? {
      brands: navigator.userAgentData.brands.map(b => ({brand:b.brand, version:b.version})),
      mobile: navigator.userAgentData.mobile, platform:navigator.userAgentData.platform
    } : null
  };
  function visible(selector) {
    if (!selector) return false;
    return [...document.querySelectorAll(selector)].some(el => {
      const style = getComputedStyle(el);
      return el.getClientRects().length > 0 && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    });
  }
  let authenticated = false, unauthenticated = false, error = null;
  try {
    authenticated = visible(options.authenticatedSelector);
    unauthenticated = visible(options.unauthenticatedSelector);
  } catch { error = 'invalid_selector'; }
  const status = error || authenticated === unauthenticated ? 'unknown' : authenticated ? 'authenticated' : 'unauthenticated';
  let fingerprint = null;
  if (globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(environment)));
    fingerprint = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,'0')).join('');
  }
  return {
    environment, fingerprint,
    session: {profileId:options.profileId ?? null, origin:location.origin},
    loginEvidence: {status, authenticated, unauthenticated, error,
      authenticatedSelector:options.authenticatedSelector || null,
      unauthenticatedSelector:options.unauthenticatedSelector || null,
      checkedAt:new Date().toISOString(), method:'visible_css_selectors'}
  };
}
