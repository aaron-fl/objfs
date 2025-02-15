from objfs.kvfs import KVStore, Filesystem, SFTP, Paper


class Client():
    def __init__(self, config=None):
        config = config or self.get_initial_config_yaml() or self.get_initial_config_json()
        if not config: raise ValueError("Could not find a suitable config file")
        self.bridges = {}
        for cfg in config.get('bridges', []):
            Bridge = {'fs':Filesystem, 'sftp':SFTP, 'paper':Paper}[cfg.pop('kind')]
            store = KVStore(**cfg.pop('kvstore'))
            self.bridges[store.id] = Bridge(store, **cfg)
            

    def __enter__(self):
        return self


    def __exit__(self, *args):
        self.close()


    def close(self):
        for bridge in self.bridges.values():
            bridge.close()


    def get_initial_config_yaml(self):
        try:
            with open(Path.home() / '.objfs' / 'config.yaml', 'r') as f:
                import yaml
                try:
                    from yaml import CLoader as Loader, CDumper as Dumper
                except ImportError:
                    from yaml import Loader, Dumper
                return yaml.load(f, Loader)
        except Exception as e:
            print(f"get_initial_config_yaml error: {e}")
            return None


    def get_initial_config_json(self):
        try:
            with open(Path.home() / '.objfs' / 'init.json', 'r') as f:
                import json
                return json.load(f)
        except Exception as e:
            print(f"get_initial_config_json error: {e}")
            return None


    def read_stream(self, store_id, key, chunk_size=None):
        bridge = self.bridges[store_id]
        bridge.connect()
        yield from bridge.read_stream(key, chunk_size=chunk_size)


from pathlib import Path
