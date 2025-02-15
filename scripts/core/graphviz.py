from pathlib import Path
from .sys_tool import SysTool
from cli import run

class GraphViz(SysTool):
    need = r'\D*8\..*'
    version_cmd = ['-V']
    cmd = lambda: Path('dot')#CLI.config_var("An absolute pathname to the `dot` command", 'dot', lambda p: Path(p))
    used_for = lambda: 'stuff'#CLI.config_var("Why is this required?", "graphviz is required.")


    @classmethod
    def install_help_macos(self):
        help = ["Install using brew:"]
        help += ["  $ brew install graphviz"]
        return help


    @classmethod
    def install_help_generic(self):
        return ["https://graphviz.org/download/"]


    def __call__(self, outfile, data=None, *, ftype=None, cmd='dot'):
        cmd = [str(self.__class__.cmd().parent / cmd)]
        if outfile != '-':
            ofile = Path(outfile)
            cmd += [f'-T{ofile.suffix[1:]}', f'-o{ofile}']

        if data:
            run(cmd, stdin='\n'.join(data) if isinstance(data,list) else data)
        else:
            run(cmd + [str(ofile.with_suffix('.dot'))])
        