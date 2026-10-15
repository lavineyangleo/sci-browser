export function compareSnapshot(previous, current) {
  if (!previous?.environment || !current?.environment) return {status:'unknown', reason:'快照缺少环境信息，不能比较。', changed:[]};
  if (previous.environment.version !== current.environment.version) return {status:'unknown', reason:'环境格式版本不同，不能比较。', changed:[]};
  const keys = Object.keys(current.environment);
  if (keys.some(key => !Object.hasOwn(previous.environment,key))) return {status:'unknown',reason:'旧快照环境字段不完整。',changed:[]};
  const canonical = value => JSON.stringify(value, function(key,item) {
    return item && typeof item === 'object' && !Array.isArray(item)
      ? Object.fromEntries(Object.keys(item).sort().map(k => [k,item[k]])) : item;
  });
  const changed = keys.filter(key => canonical(previous.environment[key]) !== canonical(current.environment[key]));
  if (previous.session?.origin !== current.session?.origin) changed.push('origin');
  if (previous.session?.profileId !== current.session?.profileId) changed.push('profileId');
  return {status:changed.length?'different':'matching', changed,
    reason:changed.length ? `差异：${changed.join('、')}` : '已记录的环境字段一致；这不保证登录有效。'};
}
