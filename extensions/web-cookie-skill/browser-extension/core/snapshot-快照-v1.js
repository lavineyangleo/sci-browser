export function snapshot(url, cookies) {
  const records = cookies.map(c => ({
    name:c.name, value:c.value, domain:c.domain.toLowerCase(), path:c.path || '/',
    expires:c.session ? null : c.expirationDate ?? null, httpOnly:!!c.httpOnly,
    secure:!!c.secure, sameSite:({strict:'Strict',lax:'Lax',no_restriction:'None'})[c.sameSite] ?? null,
    session:!!c.session, partitionKey:c.partitionKey ?? null
  })).sort((a,b) => JSON.stringify([a.name,a.domain,a.path,a.partitionKey]).localeCompare(JSON.stringify([b.name,b.domain,b.path,b.partitionKey])));
  return {schemaVersion:'1.0',sourceUrl:url,capturedAt:new Date().toISOString(),cookies:records};
}
export function mask(value) { return value ? value.length <= 6 ? '***' : value.slice(0,3)+'…'+value.slice(-2) : ''; }
