from cli import CLI


@CLI()
def cat(repo=None, key=None, /):
    ''' Dump the data of a blob to stdout

    Parameters:
        <string>, --repo <str>
            fs:/path/to/filesystem/kvstore
            kvstore_id
        <string>, --key <str>
            The key of the blob inside the specified KVStore
    '''
    config = None
    if repo.startswith('fs:'):
        config = {'bridges':[{'id':'fs', 'kind':'fs', 'base':repo[3:]}]}
        repo = 'fs'
    elif repo.startswith('sftp:'):
        username, rest = repo[5:].split('@')
        hostname, rest = rest.split(':')
        port, path = rest.split('/',1)
        config = {'bridges':[dict(kind='sftp', kvstore=dict(id='sftp', base='/'+path), port=int(port), hostname=hostname, username=username, look_for_keys=False, allow_agent=True)]}
        repo = 'sftp'
    with Client(config) as client:
        for chunk in client.read_stream(repo, key, 256):
            sys.stdout.write(chunk.decode('UTF8'))


@CLI()
def paper(key, msg=None):
    ''' Test paper bridge

    Parameters:
        <str>, --key <str>
            The key
        <str>, --msg <str>
            [optional] the message to write
    '''
    closet = StorageLocation(id="3_1", name="in closet")
    shelf = StorageLocation(id='3', name='on top shelf', location=closet)
    notebook = StorageLocation(id='3_1_0', name="in pink notebook", location=shelf)
    storage = Storage(id='p3', name="Page #3", location=notebook)
    paper = Paper(KVStore(id='0', storage=storage))
    if msg == None:
        print(paper.read(key).decode('utf8'))
    else:
        paper.write(key, msg.encode('utf8'))


import sys, paramiko
from .client import Client
from pathlib import Path
from objfs.kvfs import Filesystem, KVStore, Paper, Storage, StorageLocation
