
class Bridge():
    ''' The bridge between you and the `KVStore` that you are trying to access.

    The KVStore might be on the same machine that you are on, or it may be on a friend's computer, or somewhere else entirely.
    The bridge needed to access the store is dependent on where your code is running.
    '''
    def __init__(self, store):
        '''
        Parameters:
            store :KVStore
                The actual store that this Bridge accesses
        '''
        self.store = store
        self.cxn = None


    def connect(self):
        if self.cxn != None: return True
        self.cxn = True


    def close(self):
        self.cxn = None


    def __enter__(self):
        if self.connect(): raise ValueError("Already Connected")
        return self


    def __exit__(self, *args):
        self.close()




class Filesystem(Bridge):
    ''' This bridge accesses the local filesystem.
    Access control uses the OS user/group.
    '''

    def _open_read(self, key, chunk_size):
        return open(Path(self.store.base) / key, 'rb')


    def _open_write(self, key, size, chunk_size):
        return open(Path(self.store.base) / key, 'wb')


    def read(self, key, max_size=None):
        if max_size == None: max_size = 4096
        with self._open_read(key, max_size) as f:
            chunk = f.read(max_size)
            if f.read(1): raise ValueError(f"Data is larger than the maximum size of {max_size}")
        return chunk


    def write(self, key, data):
        with self._open_write(key, len(data), 4096) as f:
            f.write(data)


    def read_stream(self, key, chunk_size=None):
        if chunk_size == None: chunk_size = 4096
        with self._open_read(key, chunk_size) as f:
            while chunk := f.read(chunk_size):
                yield chunk


    def write_stream(self, stream, key, size, chunk_size=None):
        chunk_size = chunk_size or 4096
        with self._open_write(key, size, chunk_size) as f:
            while chunk := stream.read(chunk_size):
                f.write(chunk)




class SFTP(Filesystem):
    
    def __init__(self, store, **ssh_args):
        super().__init__(store)
        self.sftp = None
        self.hkey = None
        self.ssh_args = ssh_args
        ssh_args.setdefault('look_for_keys',False)
        ssh_args.setdefault('allow_agent', False)
        if 'pkey_file' in ssh_args:
            self.pkey_file = ssh_args.pop('pkey_file')
        if 'hkey' in ssh_args:
            kind, hkey = ssh_args.pop('hkey').split(' ')
            self.hkey = PKey.from_type_string(kind, base64.b64decode(hkey.encode('ascii')))


    def _open_read(self, key, chunk_size):
        return self.sftp.open(str(Path(self.store.base) / key), mode='rb', bufsize=chunk_size)


    def get_pkey(self):
        pkey = self.pkey_file.split(' ')
        if len(pkey) == 2: pkey.append(None)
        while True:
            try:
                return {'ssh-rsa':RSAKey}[pkey[0]](filename=pkey[1], password=pkey[2])
            except (PasswordRequiredException, SSHException):
                pkey[2] = getpass.getpass(f"Password for ssh key at {pkey[1]!r}: ")
        

    def connect(self):
        if super().connect(): return True
        try:
            self.cxn = SSHClient()
            host = f"[{self.ssh_args['hostname']}]:{self.ssh_args['port']}"
            if self.hkey:
                self.cxn.get_host_keys().add(host, self.hkey.get_name(), self.hkey)
            else:
                self.cxn.load_system_host_keys()
            self.cxn.connect(**self.ssh_args, pkey=self.get_pkey())
        except Exception as e:
            self.cxn = None
            raise e
        self.sftp = self.cxn.open_sftp()


    def close(self):
        if self.sftp != None: self.sftp.close()
        self.sftp = None
        if self.cxn != None: self.cxn.close()
        super().close()




class DataCorrupt(Exception): pass


class Paper(Bridge):
    ''' A piece of paper or similar analog storage.
    '''    

    def encode(self, version, data):
        txt = getattr(self, f'encode_{version}')(data)
        words = ''
        while len(txt) > 7:
            r = random.randint(2,7)
            words += txt[:r] + ' '
            txt = txt[r:]
        return f"{version} {words}{txt}"


    def decode(self, txt):
        txt = txt.strip()
        try:
            version, txt = txt.split(' ',1)
            decoder = getattr(self,f"decode_{version.lower()}")
            return decoder(txt.replace('\n','').replace(' ',''))
        except Exception as e:
            raise DataCorrupt(str(e))

    
    def encode_w(self, data):
        data = base64.b32encode(data + hashlib.md5(data).digest()[:8])
        pad = 0
        while data[-1-pad] == 61: pad += 1
        data = bytearray(map(lambda x:base64._b32alphabet.index(x), data[:len(data)-pad]))
        data.append(pad)
        data = RSCodec(nsym=6, c_exp=5).encode(data)
        return bytes(map(lambda x:base64._b32alphabet[x], data)).decode('ascii').lower()


    def decode_w(self, txt):
        erase_pos = []
        data = bytearray()
        for i, c in enumerate(map(ord, txt.upper().replace('0','O').replace('1','L'))):
            if c not in base64._b32alphabet:
                c = 65
                erase_pos.append(i)
            data.append(base64._b32alphabet.index(c))
        data, _, errors = RSCodec(nsym=6, c_exp=5).decode(data, erase_pos=erase_pos)
        data = base64.b32decode(bytes(map(lambda x:base64._b32alphabet[x], data[:-1])) + b'='*data[-1])
        if hashlib.md5(data[:-8]).digest()[:8] != data[-8:]: raise ValueError("Data corrupt")
        return data[:-8]


    def write(self, key, data):
        from cli import Table
        dout = self.encode('w', data)
        print(f"Find this piece of paper:\n\n{self.store.storage}\n")
        print(f"If a message titled {key!r} already exists then erase it and\nrecord the following message:")
        tbl = Table(0,0)
        tbl(key,dout)
        for row in tbl.reflow(width=40):
            print(row.replace('⤷',' '))


    def read(self, key, max_size=None):
        from cli import print
        print.ln(f"Find this piece of paper:\n\n{self.store.storage}")
        while True:
            txt = input(f"Enter the message associated with {key!r}: ")
            try:
                return self.decode(txt)
            except DataCorrupt as e:
                print.ln(print.ERR, e)


    def read_stream(self, key, chunk_size=None):
        if chunk_size == None: chunk_size = 4096
        data = io.BytesIO(self.read(key))
        while chunk := data.read(chunk_size):
            yield chunk



import io, base64, getpass, random, hashlib
from reedsolo import RSCodec
from pathlib import Path
from paramiko import SSHClient, RSAKey, PKey, PasswordRequiredException, SSHException, Agent, util
#util.log_to_file("paramiko.log")
