"""Authenticated loopback API for a dedicated Mihomo instance."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from services.mihomo.bridge.services.exit_probe import probe_exit

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / 'settings.json').read_text(encoding='utf-8'))
LOCK = threading.RLock()
PROCESS = None
STATE = json.loads((ROOT / 'state.json').read_text(encoding='utf-8'))

def validate(data):
    host = str(data.get('host', '')).strip()
    if not host or any(c in host for c in '/@?# \r\n\t'):
        raise ValueError('服务器必须是IP或主机名，不含协议和路径')
    port = int(data.get('port', 0))
    if not 1 <= port <= 65535:
        raise ValueError('端口必须为1至65535')
    user, password = str(data.get('username', '')), str(data.get('password', ''))
    if bool(user) != bool(password):
        raise ValueError('用户名和密码须同时填写，或同时留空')
    if len(user.encode()) > 255 or len(password.encode()) > 255:
        raise ValueError('SOCKS5用户名或密码超过255字节')
    return {'host': host, 'port': port, 'username': user, 'password': password}

def stop():
    global PROCESS
    if PROCESS and PROCESS.poll() is None:
        PROCESS.terminate()
        PROCESS.wait(timeout=10)
    PROCESS = None

def start(profile):
    global PROCESS
    config = {'mixed-port': 17895, 'allow-lan': False, 'bind-address': '127.0.0.1',
              'mode': 'rule', 'log-level': 'error', 'ipv6': False,
              'proxies': [dict(name='SOCKS5', type='socks5', server=profile['host'],
                               port=profile['port'], username=profile['username'],
                               password=profile['password'], udp=False)],
              'rules': ['MATCH,SOCKS5']}
    candidate = ROOT / 'candidate.json'
    candidate.write_text(json.dumps(config), encoding='utf-8')
    check = subprocess.run([SETTINGS['core'], '-t', '-d', str(ROOT / 'runtime'), '-f', str(candidate)],
                           capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    if check.returncode:
        raise ValueError('Mihomo配置校验失败')
    stop()
    with (ROOT / 'runtime/core.log').open('ab') as log:
        PROCESS = subprocess.Popen([SETTINGS['core'], '-d', str(ROOT / 'runtime'), '-f', str(candidate)],
                                   stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(.7)
    if PROCESS.poll() is not None:
        raise RuntimeError('Mihomo未能启动，请检查17895端口')

def persist():
    temp = ROOT / 'state.tmp'
    temp.write_text(json.dumps(STATE, ensure_ascii=False), encoding='utf-8')
    os.replace(temp, ROOT / 'state.json')

def handle(action, data):
    with LOCK:
        if action == '/status':
            return dict(STATE, running=bool(PROCESS and PROCESS.poll() is None))
        if action == '/apply':
            profile = validate(data)
            old = STATE['profile']
            try:
                if STATE['enabled']:
                    start(profile)
            except Exception:
                if STATE['enabled']:
                    start(old)
                raise
            STATE['profile'] = profile
            persist()
            return {'saved': True}
        if action == '/enabled':
            enabled = data.get('enabled')
            if not isinstance(enabled, bool):
                raise ValueError('开关值无效')
            start(STATE['profile']) if enabled else stop()
            STATE['enabled'] = enabled
            persist()
            return {'enabled': enabled}
        if action == '/test':
            if not PROCESS or PROCESS.poll() is not None:
                raise ValueError('请先开启代理')
            return probe_exit()
        raise ValueError('未知请求')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        if self.headers.get('Host') != '127.0.0.1:17896':
            self.send_error(403)
            return
        if not secrets.compare_digest(self.headers.get('X-Bridge-Token', ''), SETTINGS['token']):
            self.send_error(403)
            return
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 <= size <= 8192:
                raise ValueError('请求过大')
            data = json.loads(self.rfile.read(size) or b'{}')
            result = {'ok': True, 'data': handle(self.path, data)}
        except Exception as error:
            result = {'ok': False, 'error': str(error)}
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    (ROOT / 'runtime').mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 17896), Handler)
    try:
        if STATE['enabled']:
            start(STATE['profile'])
        server.serve_forever()
    finally:
        stop()
