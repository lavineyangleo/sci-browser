"""Probe real HTTPS egress through the local proxy, without direct fallback."""
import ipaddress
import subprocess


def probe_exit():
    endpoints = (
        ('Cloudflare', 'https://www.cloudflare.com/cdn-cgi/trace'),
        ('ipify', 'https://api.ipify.org'),
    )
    errors = []
    for name, url in endpoints:
        try:
            result = subprocess.run(
                ['curl.exe', '--silent', '--show-error', '--connect-timeout', '4',
                 '--max-time', '10', '--noproxy', '', '--proxy',
                 'http://127.0.0.1:17895', url, '--write-out',
                 '\n%{http_code}\n%{time_total}'],
                capture_output=True, text=True, timeout=12,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode:
                reason = {28: '连接超时', 7: '连接失败', 35: 'TLS握手失败',
                          60: 'TLS证书验证失败'}.get(result.returncode, '请求失败')
                errors.append(f'{name}: {reason}（curl {result.returncode}）')
                continue
            body, status, elapsed = result.stdout.strip().rsplit('\n', 2)
            if status.strip() != '200':
                errors.append(f'{name}: HTTP {status.strip()}')
                continue
            raw_ip = (next((line[3:].strip() for line in body.splitlines()
                            if line.startswith('ip=')), '')
                      if name == 'Cloudflare' else body.strip())
            ip = str(ipaddress.ip_address(raw_ip))
            return {'ip': ip, 'seconds': float(elapsed), 'status': '200',
                    'source': name, 'previous_errors': errors}
        except subprocess.TimeoutExpired:
            errors.append(f'{name}: 检测进程超时')
        except (ValueError, OSError) as error:
            errors.append(f'{name}: 返回格式无效或检测程序不可用（{type(error).__name__}）')
    raise RuntimeError('出口检测未成功，不代表所有网站均不可达；' + '；'.join(errors))
