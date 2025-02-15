import os
from cli import run
from .sys_tool import SysTool

class RedisServer(SysTool):
    ''' A local redis server
    '''

    version_cmd = ['--version']
    cmd = lambda: 'redis-server'
    need = r'.*?v=7\.([2-9])\..*'

   
    @classmethod
    def install_help_macos(self):
        help = ["Install using brew:"]
        help += ["  $ brew install redis"]
        return help


    @classmethod
    def install_help_generic(self):
        return ["https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/"]


    def run(self, **kwargs):
        config = dict(
            protected_mode = 'yes',
            port = 6379,
            daemonize = 'no',
            databases = 16,
            dbfilename = 'dump.rdb',
            dir = 'local/redis/',
            save = '3600 1 300 100 60 10000',
            maxmemory = '128Mb',
            maxmemory_policy = 'volatile-lfu',
        )
        config.update(kwargs)
        os.makedirs(config['dir'], exist_ok=True)
        filename = os.path.join(config['dir'],'redis.conf')
        with open(filename, 'w') as f:
            for k,v in config.items():
                f.write(f"{k.replace('_','-')} {v}\n")
        run([self.__class__.cmd(), filename])
