from cli import CLI



@CLI()
def setup():
    print.pretty(Config())


@CLI('.blobs')
def blobs(*args):
    ''' Blob related commands
    '''
    return CLI.sub_cmd(blobs, args)



@CLI()
def test(spec=None, *, verbose__v=False):
    ''' Run all unit tests

    Parameters:
        <str>, --spec <str>
            The first parameter to pytest.
            e.g. somedir/file.py::test_name
        --verbose, -v
            verbose output
    '''
    import pytest
    if Config().target != 'test':
        exit("Must execute test with the -t test target")
    args = ['--ignore', 'local'] + ['-o', 'python_files=_test_*.py']
    if verbose__v: args.append('-'+'v'*(int(verbose__v)+1))
    if spec: args.append(spec)
    ret = pytest.main(args)
    sys.exit(ret)


@CLI()
def platon(*, out__o="local/platon_graph.png", view__v=False):
    ''' Show platon graph

    Parameters:
        --out <fname>, -o <fname>
            The filename of the image to write.
        --view, -v
            Open up the created image with the system viewer.
    '''
    from scripts.core.graphviz import GraphViz
    from objfs.platon import Name, platon_graph
    lines = platon_graph(Name)
    if out__o == '-': return print.ln(lines)
    GraphViz()(out__o, lines)
    if view__v: run(['open', out__o])



import sys
from cli import print, run
from config import Config
