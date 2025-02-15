import re, os
from .git import Git
from cli import CLI, print, run
from config import Config
from ..graphviz import GraphViz


def create_graph(repo='.'):
    _safe = lambda x: re.sub(r'[\n"]', '_', x)
    g = Git(repo)
    lines = ['digraph GIT {','fontname="Helvetica";', 'node [shape=rectangle];', 'edge [arrowhead="none"];']
    seen = set()
    all_refs = {g.name:g for g in g.refs()}
    for ref in all_refs.values():
        clr = dict(branch='blue', remote='red').get(ref.kind, 'darkgreen')
        lines += [f'ref{ref.refid} [label=<<font point-size="16" color="{clr}">{html.escape(ref.short)}</font>> color={clr}];']
    for ref in all_refs.values():
        for log in g.log(ref.hash):
            if log.hash in seen: break
            seen.add(log.hash)
            if log.parent_hash: lines += [f'r{log.hash} -> r{p};' for p in log.parent_hash.split(' ')]
            lines += [f'r{log.hash} [label=<<font point-size="12" color="gray">{html.escape(log.short_hash)}</font><br/><font point-size="14">{html.escape(log.subject)}</font>>];']
    for ref in all_refs.values():
        if ref.hash in seen:
            lines += [f'ref{ref.refid} -> r{ref.hash} [arrowhead=normal];']
        else:
            lines += [f'ref{ref.refid} -> ref{all_refs[ref.hash].refid} [arrowhead=normal];']
    lines += ['}']
    return lines



@CLI()
def graph(repo, /, out__o="local/git_graph.png", type__t=None, *, view__v=False):
    ''' Create a graphviz graph of the repository commits.

    Parameters:
        <repo>, --repo <repo>
            ~parent~
        <filename>, --out <filename>, -o <filename>
            The output filename. '-' to output to stdout
        <type>, --type <type>, -t <type>
            The file output type.
            The default is to use the extension of the output file.
        --view, -v
            Open the generated image file with the system viewer.
    '''
    if out__o == '-':
        print.ln(create_graph(repo))
        return
    GraphViz()(out__o, create_graph(repo), ftype=type__t)
    if view__v: run(['open', out__o])


@CLI()
def validate_version(repo):
    ''' Ensure that config.version is changed correctly.
    
    Parameters:
        <repo>, --repo <repo>
            ~parent~
    '''
    print(Config().version)



def git_hooks_install(repo):
    ''' Install the hooks that are defined in config.py
    
    Parameters:
        <repo>, --repo <repo>
            ~parent~
    '''
    for kind, cmd in Config().git_hooks.items():      
        lines = ['#!/bin/sh', f'if ! {cmd}; then', '    exit 1','fi']
        print.ln(f"Installing {kind} hook: {cmd}")
        with open(f'{repo}/.git/hooks/{kind}', 'w') as f:
            for l in lines.split('\n'):
                f.write(l[8:]+'\n')
        os.chmod(f'{repo}/.git/hooks/pre-commit', 0o755)



import html
