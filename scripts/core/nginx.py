import sys, os
from cli import run, print, exit
from .openssl import OpenSSL


class Nginx():

    _instance = None

    def __new__(cls):
        if Nginx._instance: return Nginx._instance
        return super().__new__(cls)


    def __init__(self, cert="cert", **kwargs):
        if Nginx._instance: return
        Nginx._instance = self
        ver = None
        try:
            ver = run(['nginx', '-v'], read=True, msg='').strip()
            ver = tuple(map(int, ver.split('/')[-1].split('.')))
            assert(ver[0] >= 1)
            if ver[0] == 1: assert(ver[1] >= 21)
        except:
            if not ver:
                print.ln(print.ERR, "nginx not found")
                print.ln(' $ brew install nginx')
            else:
                print.ln(print.ERR, "Incompatable nginx found: ~lang ja~互換性のないopenssl: ", '.'.join(map(str, ver)))
            sys.exit(1)
        self.cfg = {'workers': 1, 'prefix':'local/nginx', 'port':80, 'cert': cert}
        self.cfg.update(kwargs)
        os.makedirs(self.prefix, exist_ok=True)


    def __getattr__(self, k):
        return self.cfg[k]


    def config(self, **kwargs):
        self.cfg.update(kwargs)
        if not os.path.isfile(os.path.join(self.prefix, 'mime.types')):
            run(['curl','https://raw.githubusercontent.com/nginx/nginx/master/conf/mime.types','-o',os.path.join(self.prefix, 'mime.types')])
        cfg = [
            f'worker_processes {self.workers}',
            f'pid {self.prefix}/nginx.pid',
            ('events', [
                'worker_connections 1024',
                'accept_mutex ' + ('on' if self.workers > 1 else 'off'),
            ]),
            ('http', [f'{x}_temp_path {self.prefix}' for x in ['client_body', 'proxy', 'fastcgi','uwsgi','scgi']] + 
            [f'proxy_set_header {x} {y}' for x,y in {'X-Forwarded-Host':'$server_name','X-Real-IP':'$remote_addr', 'X-Forwarded-For':'$proxy_add_x_forwarded_for', 'X-Forwarded-Proto':'$scheme', 'Host':'$http_host'}.items()] + [
                "log_format dev '[$status] $upstream_response_time $http_host $request'",
                f'access_log {self.prefix}/nginx.log dev',
                'sendfile on',
                'proxy_redirect off',
                'keepalive_timeout 5',
                'proxy_read_timeout 3600',
                'client_max_body_size 10M',
                'include mime.types',
                'server_names_hash_bucket_size 64',
            ]),
            
        ]
        if self.cert:
            cfg[-1][1].append(f'ssl_certificate {self.cert}.pem')
            cfg[-1][1].append(f'ssl_certificate_key {self.cert}-key.pem')
            if self.port == 80:
                cfg[-1][1].append(('server', ['listen 80', 'server_name _', 'return 301 https://$host$request_uri']))
        for domain, locs in self.domains.items():
            srv = [
                f'listen {443 if self.cert and self.port == 80 else self.port}' + (' ssl' if self.cert else ''),
                f"server_name {domain}{domain and '.' or ''}dev.localhost",
               
            ]
            for x in locs:
                if isinstance(x, tuple):
                    #d = f'proxy_pass {x[1]}' if x[1].startswith('http') else x[1]
                    srv.append((f'location {x[0]}', x[1:]))
                else:
                    srv.append(x)
            if '/' not in [x[0] for x in locs if isinstance(x, tuple)]:
                srv.append(('location /', ['try_files $uri $uri.html $uri/ /index.html']))
            cfg[-1][1].append(('server', srv))

        with open(os.path.join(self.prefix, 'nginx.conf'), 'w') as f:
            def clean(x, depth=0):
                for l in x:
                    if isinstance(l, tuple):
                        yield ' '*4*depth + l[0] + ' {\n'
                        yield from clean(l[1], depth+1)
                        yield ' '*4*depth + '}\n'
                    else:
                        yield ' '*4*depth + l + ';\n'
            f.write(''.join(clean(cfg)))
    

    def run(self):
        OpenSSL().ensure_server_cert(f"{self.prefix}/{self.cert}")
        run(['nginx', '-c', f'{self.prefix}/nginx.conf', '-p', os.path.abspath('.'), '-e', 'stderr'])


    def stop(self):
        run(['nginx', '-s', 'stop', '-c', f'{self.prefix}/nginx.conf', '-p', os.path.abspath('.')])


