import os, re
from cli import CLR, print, exit, run, UsageError, Text
from .singleton import Singleton


class MissingTool(UsageError):
    def __init__(self, tool, got):
        import platform
        msg = []
        if hasattr(tool, 'used_for'):
            msg += [tool.used_for()]

        msg = [Text(f"{CLR.y}{tool.__mro__[1].__name__}{CLR.x} requires version >= {CLR.m}{tool.need}{CLR.x}"), '']

        if not got:
            msg += [f'{print.ERR} No version was found.', '']
        else:
            msg += [f'Version {CLR.r}{got}{CLR.x} was found.', '']


        pfm = 'install_help_' + platform.platform().lower().split('-')[0]
        msg += tool.install_help_generic()
        if hasattr(tool, pfm): msg += [''] + getattr(tool, pfm)()
        super().__init__(*msg)
        



class SysTool(metaclass=Singleton):

    @classmethod
    def version_fail(self, have, need):
        print.ln(print.ERR, f"Invalid version for {self.__name__.split('__')[0]}", ['']*2, f"have: {have}", ['']*2, f"need: {need}")
        exit(1)


    @classmethod
    def init_once(self, need=None, **kwargs):
        need = need or self.need
        version = run([str(self.cmd())] +self.version_cmd, silent=True, read=True, or_else='').strip()
        if not re.match(need, version, re.I):
            raise MissingTool(self, version)
        

    def __call__(self, *args, **kwargs):
        print(f"__Call__ {args} {kwargs}")
