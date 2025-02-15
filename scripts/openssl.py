import logging, os, sys, re
from cli import print, run, exit, CLR, Text
from datetime import datetime
log = logging.getLogger('secrets')



class OpenSSL():

    _instance = None

    def __new__(cls):
        if OpenSSL._instance: return OpenSSL._instance
        return super().__new__(cls)


    def __init__(self):
        if OpenSSL._instance: return
        OpenSSL._instance = self
        self.openssl = os.path.join(os.environ.get('OPENSSL3', '/usr/local/opt/openssl/bin'), 'openssl')
        if not os.path.exists(self.openssl):
            self.openssl = 'openssl'
        try:
            ver = run([self.openssl, 'version', '-v'], read=True, or_else='Unknown ', msg='').split(' ')
            assert(ver[0] == 'OpenSSL')
            assert(ver[1][0] == '3')
        except:
            print.ln(print.ERR, "Incompatable openssl found: ~lang ja~互換性のないopenssl: ", ' '.join(ver))
            print.ln("Get OpenSSL 3.x and / or set OPENSSL3 and try again.~lang ja~OpenSSL 3.xを入手して、再試行してください。 PATHにopensslがなければ「OPENSSL3」の環境変数の設定が必要",)
            exit("   $ brew install openssl")


    def cert_show(self, prefix, mode='-subject'):
        run([self.openssl, 'x509', '-in', prefix+'.pem', mode, '-noout'])


    def expires(self, prefix):
        val = run([self.openssl, 'x509', '-enddate','-noout','-in', prefix+'.pem'], read=True)
        return (datetime.strptime(val.split('=',1)[1].strip(), "%b %d %H:%M:%S %Y %Z") - datetime.now()).days


    def cert(self, *, prefix, cn, ca, san=[], client=False, force=False, askpass=False, days=365):
        log.info(f"Openssl '{prefix}'  {ca}  {cn}  {san}")

        if not force and os.path.exists(prefix+'.pem'):
            self.cert_show(prefix, '-text')
            exit(print.ERR, "Certificate exists.  Use `--force` to overwrite")
        os.makedirs(os.path.split(prefix)[0], exist_ok=True)
        subj=f'/O=cli.py/CN={cn}'
        #subjcn = ''.join([f'/CN={cn}' for cn in cn if '*' not in cn])
        sancn = ','.join([f'IP:{x}' if re.search(r'^[0-9.:]+$',x) else f'DNS:{x}' for x in san])

        cmd = [self.openssl, 'req', '-x509', '-sha256', '-out', prefix+'.pem', '-newkey', 'rsa:2048', '-keyout', prefix+'-key.pem', '-days', str(days), '-subj', subj]
        if not askpass:
            cmd += ['-noenc']
        if ca:
            cmd += ['-CA', ca+'.pem']
            cmd += ['-CAkey', ca+'-key.pem']
            cmd += ['-addext', 'basicConstraints=critical,CA:FALSE']
            cmd += ['-addext', 'subjectKeyIdentifier=none']
            if client:
                cmd += ['-addext', 'extendedKeyUsage=clientAuth']
            else:
                #Key Usage: critical, Digital Signature, Key Encipherment
                cmd += ['-addext', 'extendedKeyUsage=serverAuth']
        else:
            cmd += ['-addext', 'basicConstraints=critical,CA:TRUE']
            cmd += ['-addext', 'keyUsage=critical,keyCertSign']
            cmd += ['-addext', 'subjectKeyIdentifier=hash']
            cmd += ['-addext', 'authorityKeyIdentifier=none']
        if sancn:
            cmd += ['-addext', f'subjectAltName={sancn}']
        
        
        run(cmd)
        self.cert_show(prefix)


    def rsa(self, *, path, format):
        run([self.openssl, 'genrsa', '-traditional', '-out', path])


    def hex(self, *, path, nbytes=32):
        run([self.openssl, 'rand', '-hex', '-out', path, str(nbytes)])


    def file_hash(self, fname):
        return bytes.fromhex(run([self.openssl, 'dgst', '-sha256', '-hex', '-r', fname], read=True, msg='', or_else='').split(' ',1)[0])


    def ensure_server_cert(self, prefix):
        import socket, sys
        if os.path.exists(f'{prefix}.pem'):
            if self.expires(prefix) > 0: return
            print.ln(f"Server certificate is expired.")
        default_ca = f"~/ca_{socket.gethostname().split('.')[0]}"
        while True:
            print.hr()
            print.ln("This will create a CA certificate so that localhost certificates will be accepted by browsers.\nIf you already have one enter the path to it, otherwise just push enter to create a new on in the default location.~lang ja~これにより CA 証明書が作成され、localhost 証明書がブラウザで受け入れられるようになります。\nすでに持っている場合はそのパスを入力し、そうでない場合は Enter キーを押してデフォルトの場所に新しいものを作成します。")
            ca = input(f"CA certificate location [{default_ca}]: ")
            ca = os.path.expanduser(ca)
            if ca and not os.path.exists(f'{ca}.pem'):
                print(print.ERR + f"'{ca}' Not found")
                continue
            if not ca: ca = os.path.expanduser(default_ca)
            if not os.path.exists(f'{ca}.pem'):
                print.ln(f"CA {ca} does not exist")
            elif self.expires(ca) < 2:
                print.ln(f"CA {ca} has expired")
            else:
                break
            print(f"Creating Certificate authority '{ca}'")
            self.cert(prefix=ca, askpass=False, days=365, ca=None, cn='localhost-ca', force=True)
            run(f'sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {ca}.pem',
                msg = Text(f'''Adding {ca}.pem to your System.keychain.\nIt will ask for your root password for sudo.
                        ~lang ja~System.keychainに「{ca}.pem」を追加します。 sudoのrootパスワードを要求されます。'''))
            break
        print(f"Creating server certificate at '{prefix}' from ca '{ca}'")
        self.cert(prefix=prefix, askpass=False, days=self.expires(ca)-1, cn='nginx-server', ca=ca, san=['localhost','127.0.0.1','dev.localhost','*.dev.localhost'])
