#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# This file may be executed with python 2.7 if the user's system is old.
# So its syntax must be python2 compatible.  
from __future__ import print_function

ENV_PREFIX = "CLIPY_" # For passing config variables via environment variables
REQ_FILE = "scripts/requirements"  # Location of requirements.txt and .lock
# This is the python import path to the initial scripts module
CLI_ENTRY_MODS = ['scripts.main', 'scripts.core.grep', 'scripts.core.git', 'scripts.core.docs']


if __name__ == '__main__':
    # This code might run on python2 so it has to be written carefully
    #
    import os, sys, hashlib, inspect

    def hash_file(fname):
        md5 = hashlib.md5()
        try:
            with open(fname,'rb') as f:
                for data in iter(lambda: f.read(4096), b''):
                    md5.update(data)
            return md5.hexdigest()
        except:
            return ''

    def _run2(cmd, capture=False, or_else=None, returns=[0]):
        import subprocess
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE if capture else None)
            resp = (proc.communicate()[0] or b'').decode('utf8').strip()
            return resp if capture else proc.returncode
        except Exception as e:
            print(e)
            return or_else

    def setup_venv(venv_dir, reqtxt_hash):
        if not os.path.exists('local'): os.makedirs('local') # exists_ok is only for newer python versions
        verify_python_version()
        print("Setting up new Python virtual environment... \n")
        assert(_run2(['python3', '-m', 'venv', venv_dir]) == 0), ('python3 -m venv '+venv_dir)
    # pip upgrades
        pip = [os.path.abspath(os.path.join(venv_dir, 'bin', 'python')), '-m', 'pip']
        assert(_run2(pip+['install', '-U', 'pip', 'wheel', 'setuptools']) == 0), "pip upgrade"
    # Should we use the lock file or txt file?
        try:
            with open(REQ_FILE+'.lock') as f:
                assert(f.readline().strip()[1:] == reqtxt_hash)
            ext = '.lock'
        except:
            ext = '.txt'
        assert(_run2(pip+['install', '--compile', '-r', REQ_FILE+ext]) == 0), "pip install"
    # If we installed with the .txt then re-create the lock file
        if ext == '.txt':
            lockdata = _run2(pip+['freeze', '--local', '-r', REQ_FILE+'.txt'], capture=True)
            assert(lockdata), 'pip freeze'
            with open(REQ_FILE+'.lock', 'w') as f:
                f.write('#'+reqtxt_hash+'\n')
                f.write(lockdata)
    

    def verify_python_version():
        import re
        with open(REQ_FILE+'.txt') as f:
            python_re = re.compile(f.readline()[1:-1], re.IGNORECASE)
            reqhash = f.readline()[len('# reqhash = '):].rstrip()
        version = _run2(['python3', '--version'], capture=True, or_else='')
        if python_re.match(version): return reqhash
        print("\x1b[0;31mIncompatible Python version\x1b[0m")
        print("Have: " + version)
        print("Need: " + python_re.pattern)
        have = _run2(['pyenv','versions','--bare'], capture=True)
        if have == None:
            print('\nInstall pyenv to manage different python versions and try again:')
            print('   $ \x1b[0;33mbrew install pyenv\x1b[0m\n')
            print('   $ \x1b[0;33meval "$(pyenv init -)"\x1b[0m\n')
            sys.exit(128)
        version = ([v.strip() for v in have.split('\n') if python_re.match(v.strip())] or [''])[-1]
        if not version:
            version = ([v.strip() for v in _run2(['pyenv','install','--list'], capture=True).split('\n') if python_re.match(v.strip())] or [''])[-1]
            if not version:
                print("\x1b[0;31mNo good version found in pyenv.  You'll have to manually install it.\x1b[0m")
                sys.exit(1)
            print('\n\x1b[0;33mInstalling python version ' + version + '\x1b[0m\n')
            _run2(['pyenv', 'install', version])
        print('\nSetting python version \x1b[0;33m' + version + '\x1b[0m into .python-version')
        _run2(['pyenv', 'local', version])
        print('\nRun the cli.py command again to use the new python.\x1b[0m\n')
        print('   $ \x1b[0;33m' + ' '.join(sys.argv) + '\x1b[0m\n')
        sys.exit(1)

# Change to the directory where the .clipy is located (so all scripts know where they are)
    script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    os.chdir(script_path)
    args = sys.argv[1:]
# A hash of requirements.txt.  This file must exists (obviously)
    reqtxt_hash = hash_file(REQ_FILE+'.txt')
    if not reqtxt_hash:
        print("\x1b[0;31mFile not found:\x1b[0m " + REQ_FILE+'.txt')
        sys.exit(1)
# The virtual environment lives in the directory given by the req.txt hash
    venv_dir = os.path.join('.python', reqtxt_hash)
    if not os.path.isdir(venv_dir): setup_venv(venv_dir, reqtxt_hash)
# We have a virtual environment.  Are we in it?
    if not args or args[0] != '~!virtual!~':
        # Switch to the virtual environment python
        os.environ['PATH'] = os.path.abspath(os.path.join(venv_dir, 'bin')) + os.pathsep + os.environ['PATH']
        os.execvp('python', ['python', '-u', '-B', '-s', './cli.py', '~!virtual!~'] + args)
# We are in the virtual environment
    args = args[1:] or ['setup'] # Get rid of ~!virtual!~


# The code from here is executed with the virtual environment 
# python 3.x and requirements.txt installed
#_______________________________________________________________________
import os, sys, inspect, re, importlib, subprocess
import importlib.util
from threading import current_thread
from functools import reduce


class UsageError(Exception):
    def __init__(self, *args):
        super(UsageError, self).__init__(*args)


def CLI(*subs):
    def _register_cli(fn):
        if os.environ.get(ENV_PREFIX+'CLIPY_COMMANDS','y').lower() != 'n': CommandDfn(fn, subs)
        return fn
    return _register_cli



class Command():
    null = '-!!null!!-'

    def __init__(self, args):
        self.vals = {}
        self.errors = []
        for p in self.pos:
            self.get_pos_arg(p, args)
        while self.get_kw_arg(args): pass
        self.args = list(args)
        if args and not self.var: self.errors += [Text("Unusuable extra arguments: ~lang ja~使用できない余分な引数: ", ' '.join(self.args))]


    def get_pos_arg(self, p, args):
        if not args or not re.match(r'((-)?\d.*)|([^-].*)', args[0]): return
        self[p] = args.pop(0)


    def get_kw_arg(self, args):
        if not args or not args[0].startswith('-'): return False
        ks = args.pop(0)
        is_long = ks.startswith('--')
        ks = [ks[2:].replace('-','_')] if is_long else list(ks[1:])
        for k in ks:
            if k not in self.alias:
                self.errors += [Text('Unknown parameter: ~lang ja~不明なパラメータ: ', '%s%s'%('--' if is_long else '-', k))]
                continue
            key = self.alias[k]
            self[key] = True if len(ks) > 1 or self.type_of(key) == bool else args.pop(0) if args else Command.null
        return True


    def __getitem__(self, key):
        return self.vals[key]


    def __setitem__(self, key, val):
        if val == Command.null:
            self.kw[key] = Command.null
            return
        typ = self.type_of(key)
        try:
            if isinstance(typ, list):
                if isinstance(val, list):
                    self.vals[key] = list(val)
                else:
                    self.vals.setdefault(key, [])
                    assert(isinstance(val, str))
                    self.vals[key].append(val)
                return
            else:
                assert(type(val) != bool or typ == bool)
                assert(val != None)
                val = typ(val)
        except:
            if val != None:
                self.errors += [Text('''Parameter '{k}' type mismatch.  Couldn't coerce '{v}' to '{t}'.
                    ~lang ja~パラメータ「{k}」タイプの不一致。「{v}」を 「{t}」に強制出来ない。'''.format(
                        k=key, v=val, t='str' if isinstance(typ,list) else typ.__name__))]
        self.vals[key] = val


    def assert_runnable(self):
        for k in self.kw:
            if k not in self.vals:
                if self.kw[k] == Command.null:
                    if k in self.pos:
                        self.errors += [Text("No value supplied for positional parameter '{p}'~lang ja~位置パラメータ「{p}」に値が指定されてない".format(p=k))]
                    else:
                        self.errors += [Text("No value supplied for keyword parameter '{p}'~lang ja~キーワードパラメータ「{p}」に値が指定されてない".format(p=k))]
                else:
                    self[k] = self.kw[k]
        if self.errors: self.errors += ['', Text(print.ERR, '''Run with -h or --help for additional documentation for this command.
            ~lang ja~このコマンドのドキュメントについては、-hまたは--helpを指定して実行してください。'''), '']
        if self.errors or '' in self.vals:
            raise UsageError(*self.errors)


    def run(self):
        self.assert_runnable()
        args = [self.vals[x] for x in self.pos] + self.args
        kwargs = {k:v for k,v in self.vals.items() if k not in self.pos}
        if inspect.iscoroutinefunction(self.fn):
            import asyncio
            loop = asyncio.get_event_loop()
            try:
                return loop.run_until_complete(self.__class__.fn(*args, **kwargs))
            except KeyboardInterrupt:
                sys.stdout.write('\r  \n')
                sys.exit(1)

        else:
            return self.__class__.fn(*args, **kwargs)


    def type_of(self, key):
        typ = self.types[key] if key in self.types else type(self.kw[key])
        return str if typ == type(None) else [] if typ == list else typ


    def __str__(self):
        s =  "%s%s: %s\n"%(self.name if self.fn else None, '*' if self.var else '', self.pos)
        for k in self.kw:
            s += "\t%s %s : %s  %s\n"%(self.type_of(k), k, self.kw[k], self.vals.get(k, '----'))
        s += '\t*args = %s'%(self.args)
        return s




class CommandDfn(type):
    def __new__(cls, fn, subs, name='', module_path='', kw={}):
        name = fn.__name__.split('.')[-1] if fn else name
        while name[0] == '_': name = name[1:]
        module_path = fn.__module__ if fn else module_path
        cmds = current_thread().cmds
        cmds.setdefault(module_path, {})
        if name in cmds[module_path]: return cmds[module_path][name]

        cmddfn = type.__new__(cls, name, (Command,), {
            'name':name,
            'module_path':module_path,
            'pos': [],
            'var': True,
            'alias': {'help':'','h':''},
            'types': {'':bool},
            'kw':kw,
            'fn':fn,
            'sub_module_paths':subs,
        })
        cmds[module_path][name] = cmddfn
        return cmddfn


    def __init__(self, fn, *args, **kwargs):
        self.set_alias(self.kw)
        if self.fn: self.get_argspec()


    def get_argspec(self):
        spec = inspect.getfullargspec(self.fn)
        self.types.update(spec.annotations)
        if spec.varkw: raise Exception("Function '%s' should not define **%s"%(self.fn.__name__, spec.varkw))
        self.var = bool(spec.varargs)
        self.pos = spec.args
        defaults = spec.defaults or tuple()
        self.kw = {k:Command.null for k in spec.args + spec.kwonlyargs}
        self.set_alias(self.kw)
        self.kw.update(dict(zip(spec.args[-len(defaults):], defaults)))
        self.kw.update(spec.kwonlydefaults or {})
        self.docstr = '' if not hasattr(self.fn, '__doc__') else (self.fn.__doc__ or '').strip()


    def error(self, *msg):
        print.box(self.doc_lines, width=print.w)
        print.ln(CLR.o, self.fn.__code__.co_filename,':',self.fn.__code__.co_firstlineno, CLR.x, '  ', self.name)
        exit(print.ERR, *msg)


    def doc(self):
        doc = DocText(dfn=self)
        self.doc_lines = Text.unindent(self.docstr.replace('\t', '   '))
        self.doc_args = {'':0}
        doc.parse(0, 0, self.doc_lines)
        for k in self.kw:
            for k in k.split('__'):
                if k.replace('_','-') not in self.doc_args: self.error('Undocumented paramter: ', k)
        for k in self.doc_args:
            if not k:
                lpos = 0 if self.name == 'cli' else len(self.pos)
                if self.doc_args[k] != lpos and self.doc_args[k] != lpos + int(self.var):
                    self.error("Documented positional arguments doesn't match number of positional args: %s!=%s"%(self.doc_args[k], lpos))
            elif k.replace('-','_') not in self.alias:
                self.error('Documentation for non-existant parameter: ', k)
        return doc


    def set_alias(self, kw):
        for k in self.kw:
            for a in k.split('__'):
                if a in self.alias: raise Exception("Function '%s' has multiple definitions for alias '%s' in parameter '%s'"%(self.fn.__name__, a, k))
                self.alias[a] = k


    def sub_commands(self):
        thd = current_thread()
        paths = [importlib.util.resolve_name(sp, self.module_path.rsplit('.',1)[0]) if sp.startswith('.') else sp for sp in self.sub_module_paths]
        all(importlib.import_module(p) for p in paths if p not in thd.cmds)
        cmds = {}
        for p in paths:
            cmds.update(thd.cmds.get(p, {}))
        return cmds


    def __str__(self):
        return '%s.%s %s %s %s'%(self.module_path, self.name, self.pos, self.kw, self.sub_module_paths)




class ProgressBar():
    def __init__(self, **kwargs):
        self.stream = kwargs.get('stream', sys.stdout)
        self.width = kwargs.get('width',40)
        self.step_i = 0
        self.steps = kwargs.get('steps',0)
        self.prev_len = 0


    def bar(self, done, *msg):
        if done:
            bar = CLR.g + '━'*self.width
        elif not self.steps:
            w = self.width // 4
            i = self.step_i%w
            bar = CLR.a + '━━━━'*i +' '+ CLR.y + '━━ ' + CLR.a  + '━━━━'*(w-i-1)
        else:
            prog = int(min(1.0, self.step_i/self.steps)*self.width)
            bar = CLR.y + '━'*prog + ' '+ CLR.a + '━'*(self.width-prog-1)
        txt = bar + CLR.x + '  ' + str(Text(*msg)) + ' '
        txt += ' '*(self.prev_len - len(txt))
        self.prev_len = len(txt)
        return txt


    def step(self, *parts):
        self.stream.write('\r ' + self.bar(False, *parts))
        self.stream.flush()
        self.step_i += 1


    def done(self, *parts):
        self.stream.write('\r ' + self.bar(True, *parts) + '\n')




class Text(list):
    @staticmethod
    def unindent(p):
        # Unindent multi-line strings
        newlines = p.strip().splitlines()
        indent = ''
        for line in newlines[1:]: # The first line is skipped because it starts right after the opening '''
            stripped = line.lstrip()
            if stripped: # First non-blank line sets the indentation level
                indent = line[:len(line)-len(stripped)]
                break
        n_indent = len(indent)
        if indent: newlines = [l[n_indent:] if l.startswith(indent) else l for l in newlines]
        return newlines


    @staticmethod
    def l10n(p):
        lang = os.environ.get('CLIPY_LANG', 'en')
        if lang in p: p = p[p.index(lang)+len(lang):]
        return p.split('~lang',1)[0]


    def __init__(self, *msg, **kwargs):
        self.wrap = kwargs.get('wrap', True)
        self.indent = kwargs.get('indent', '')
        self.color = kwargs.get('color', '')
        if msg: self(*msg)
    

    def width(self):
        return max(map(lambda l: ConsoleBuffer.guessw(l.rstrip()), self)) if self else 0
        

    def __str__(self):
        return '\n'.join(self)


    def __call__(self, *msg):
        self.append('')
        for m in msg:		
            if isinstance(m, str):
                m = Text.l10n(m)
                newlines = Text.unindent(m) if '\n' in m else [m]
            else:
                newlines = []
                try:
                    m = map(str, m)
                except:
                    m = [str(m)]
                for n in m:
                    newlines += n.split('\n')
            newlines = [l.replace('\t','    ') for l in newlines]
            if not newlines: continue
            self[-1] += newlines[0]
            self += newlines[1:]
        return self


    def reflow(self, width=0, height=0, **kwargs):
        body = []
        min_brk = max(width - 15, 15)
        width = width and max(4, width - ConsoleBuffer.guessw(self.indent))
        def _grp(c):
            if c in '0123456789.０１２３４５６７８９': return 1
            c = ord(c)
            if c >= 0x3040 and c <= 0x309F: return 2
            if c >= 0x30A0 and c <= 0x30FF: return 3
            return 4

        def _brk(line, i):
            if line[i] in '\'",': return 2
            if line[i] in ' 　「' or line[i-1] in '。、！？': return 3
            if _grp(line[i-1]) != _grp(line[i]): return 2
            return 1

        def _wrap(line):
            i = w = bi = bw = bs = 0
            while i < len(line):
                if w > min_brk:
                    b = _brk(line, i)
                    if b >= bs: bs,bw,bi = b,w,i
                cw = _wcswidth(line[i])
                w += cw
                if w < width or i == len(line)-1 and w == width:
                    i += 1
                    continue
                # Can't fit i on this line
                w -= cw
                if width <= 4 or not self.wrap: # No wrap
                    #body.append((w+1, line[:i]+'…'))
                    return '', line[:i]+'…'
                if bs: # Rewind to the last break point
                    i, w = bi,bw
                #body.append((w, line[:i]))
                return '⤷ ' + line[i:].lstrip(), line[:i]
            return '', line
            #body.append((w,line))
        rout = 0
        for line in self:
            line = line.rstrip().replace('\t','    ')
            if not width or _wcswidth(line) <= width:
                rout += 1
                yield self.indent+self.color+line+(CLR.x if self.color else '')
            else:
                #return body.append((linew if linew >=0 else ConsoleBuffer.guessw(line), line))
                while line:
                    line, short = _wrap(line)
                    if short:
                        rout += 1
                        yield self.indent+self.color+short+(CLR.x if self.color else '')

        while rout < height:
            rout += 1
            yield self.indent




class TextPrefix(Text):
    def __init__(self, *msg, **kwargs):
        self.tmb = (kwargs.get('top',kwargs.get('mid','')), kwargs.get('mid',''), kwargs.get('end',kwargs.get('mid','')))
        self.tmbw = max(map(lambda l: ConsoleBuffer.guessw(l), self.tmb))
        super().__init__(*msg, **kwargs)


    def width(self):
        return self.tmbw + super().width()


    def reflow(self, width=0, height=0, **kwargs):
        lines = list(super().reflow(width and max(1,width-self.tmbw), height))
        last = len(lines)-1
        for i, line in enumerate(lines):
            yield self.tmb[i and (2 if i == last else 1)] + line




class Box():
    default_border = '┌┐└┘─│'

    def __init__(self, *msg, **kwargs):
        self.just = kwargs.get('just', '^<')
        self.sides = kwargs.get('sides', 15) # top right bottom left
        self.border = kwargs.get('border', Box.default_border)
        self.height = kwargs.get('height', 0)
        self.body = Text(*msg, **kwargs)


    def __call__(self, *msg):
        self.body(*msg)


    def __len__(self):
        return self.height or (len(self.body) + (self.sides>>3&1) + (self.sides>>1&1))

    
    def __bool__(self):
        return bool(self.body)


    def width(self):
        return self.body.width() + (self.sides>>2&1) + (self.sides&1)


    def reflow(self, width=0, height=0, **kwargs):
        sides = self.sides
        #sides = self.sides & 10 if width and width < 3 else self.sides
        #sides = sides & 5 if height and height < 3 else sides
        T,R,B,L = [sides>>i&1 for i in range(3,-1,-1)]
        body_w = width and width-R-L
        body = [(ConsoleBuffer.guessw(l), l) for l in self.body.reflow(body_w)]
        height = (height or self.height or (len(body)+T+B)) -T-B

        # horizontal justification
        maxw = body_w or reduce(lambda a, l: max(a,l[0]), body, 0)
        def _just(line, just):
            pre = ' '*{'<':0, '.':(maxw-line[0])//2, '>':(maxw-line[0])}[just]
            return pre + line[1] + ' '*(maxw-line[0]-len(pre))
        body = [_just(l, self.just[1]) for l in body]
        if height and len(body) > height:
            overflow = '⋮%s'%(len(body)-height+1)
            body = body[:height-1] + [_just((len(overflow), overflow), '.')]
        # vertical justification
        pad_height = height - len(body)
        pad_start = [] if pad_height <= 0 else [' '*maxw]*{'^':0, '.':pad_height//2, '_':pad_height}[self.just[0]]
        pad_end = [] if pad_height <= 0 else [' '*maxw]*(height - len(pad_start) - len(body))

        if T: yield (self.border[0] if L else '') + self.border[4]*maxw + (self.border[1] if R else '')
        for line in pad_start + body + pad_end:
            yield (self.border[5] if L else '') + line + (self.border[5] if R else '')
        if B: yield (self.border[2] if L else '') + self.border[4]*maxw + (self.border[3] if R else '')




class DefaultCell(Box): pass

    

class Table():
    default_border = '┌┬┐├┼┤└┴┘─│'

    def __init__(self, *cols, **kwargs):
        self.stream = kwargs.get('stream', sys.stdout)
        self.ncols = len(cols)
        self.col_widths = cols
        self.col_color = [kwargs.get('color%s'%i, kwargs.get('color', '')) for i in range(self.ncols)]
        self.col_border = [kwargs.get('border%s'%i, kwargs.get('border', Table.default_border))+' '*11 for i in range(self.ncols)]
        self.col_just = [kwargs.get('just%s'%i, kwargs.get('just', '^<')) for i in range(self.ncols)]
        self.col_sides = [kwargs.get('sides%s'%i, kwargs.get('sides', 0x3f)) for i in range(self.ncols)]
        assert(self.ncols)
        self.rows = []


    def __bool__(self):
        return bool(self.rows)


    def __len__(self):
        return len(list(self.reflow()))


    def width(self):
        try:
            return ConsoleBuffer.guessw(next(iter(self.reflow())))
        except:
            return 0


    def reflow(self, width=0, height=0, **kwargs):
        if not self.rows: return
        # Add bottom borders
        for i, c in enumerate(self.rows[-1]):
            if not isinstance(c, DefaultCell): continue
            c.sides |= 2 if self.col_sides[i] & 2 else 0
        # Resolve widths
        def _w0(col_i):
            return max(map(lambda r: r[col_i].width(), self.rows))
        if width:
            widths = [_w0(i) if c <= 0 else int(width*c) if c < 1 else c for i,c in enumerate(self.col_widths)]
            free = width - sum(widths)
            # Shrink columns
            while free < 0:
                widths[widths.index(max(widths))] -= 1
                free += 1
            # split extra space between negative columns
            frac = sum([-x for x in self.col_widths if x < 0] or [0])
            for i, c in enumerate(self.col_widths):
                if c >= 0: continue
                widths[i] = int(-c*free/frac)
            # Allocate superfluous space to the last column
            widths[i] += width - sum(widths)
            assert(sum(widths) == width)
        else:
            widths = [_w0(i) for i in range(self.ncols)]
        #
        hout = 0
        for row in self.rows:
            lines = [list(o.reflow(width=w)) for w,o in zip(widths, row)]
            h = max(map(len, lines))
            lines = [list(o.reflow(width=w, height=h)) for w,o in zip(widths, row)]
            for r in range(h):
                hout += 1
                yield ''.join([lines[c][r] for c in range(self.ncols)])
        end = ' '*ConsoleBuffer.guessw(''.join([lines[c][0] for c in range(self.ncols)]))
        while hout < height:
            hout += 1
            yield end
        

    def reset(self):
        self.rows = []			


    def __call__(self, *objs, **kwargs):
        def _add(obj):
            if not self.rows or len(self.rows[-1]) % self.ncols == 0:
                self.rows.append([])
            self.rows[-1].append(obj)
        for o in objs:
            if isinstance(o, DefaultCell) or not hasattr(o, 'reflow'):#isinstance(o, Box):
                col = (len(self.rows[-1]) if self.rows else 0)%self.ncols
                csides = kwargs.get('sides', self.col_sides[col])
                cborder = kwargs.get('border', self.col_border[col])
                just = kwargs.get('just', self.col_just[col])
                color = kwargs.get('color', self.col_color[col])
                sides = 0
                Rf, Cf, Cl = (not self.rows or len(self.rows)==1 and len(self.rows[0]) < self.ncols, col==0, col==self.ncols-1)
                border = cborder[0 if Rf and Cf else 1 if Rf else 3 if Cf else 4]
                border += cborder[2 if Rf else 5]
                border += cborder[6 if Cf else 7] + cborder[8]
                border += cborder[9:]
                sides += 1 if csides&(1 if Cf else 16) else 0 # Left edge
                sides += 8 if csides&(8 if Rf else 32) else 0 # Top edge
                sides += 4 if csides&4 and Cl else 0 # right edge
                if isinstance(o, DefaultCell):
                    o.sides, o.border, o.just = sides, border, just
                else:
                    o = DefaultCell(*(o if isinstance(o, tuple) else (o,)), sides=sides, border=border, just=just, color=color)
            _add(o)


class Color():
    def __init__(self):
        self.color_on = True

    def __getattr__(self, a):
        if not self.color_on: return ''
        a = {'a':'1;30', 'la':'0;37', 'r':'0;31', 'lr':'1;31', 'g':'0;32', 'lg':'1;32', 'o':'0;33','y':'1;33','b':'0;34','lb':'1;34','m':'0;35', 'lm':'1;35', 'c':'0;36', 'lc':'1;36', 'bld':'1','w':'1','x':'0'}[a]
        return '\x1b['+a+'m'

CLR = Color()	
    
_wcswidth = lambda x: len(x)

class ConsoleBuffer():
    color_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    @classmethod
    def guessw(self, s):
        s = self.color_escape.sub('', s)
        w = _wcswidth(s)
        return len(s) if w < 0 else w


    def __init__(self, stream):
        self.set_stream(stream)
        self.set_doc_lang(False,False)
        self.blank = {}


    def set_doc_lang(self, en, ja):
        if en or ja:
            os.environ['CLIPY_LANG'] = '~lang ' + ('en' if en else 'ja') + '~'
        else:	
            os.environ.setdefault('CLIPY_LANG', '~lang ' + ('ja' if 'ja' in os.environ.get('LANG', '') else 'en') + '~')



    def set_stream(self, stream):
        self.stream = stream
        try:
            ConsoleBuffer.w = os.get_terminal_size().columns - 1
        except:
            ConsoleBuffer.w = 79

        try:
            from wcwidth import wcswidth
            global _wcswidth
            _wcswidth = wcswidth
        except:
            pass
        
        CLR.color_on = os.environ.get("CLIPY_COLOR", 'y' if self.stream.isatty() else 'n').lower() == 'y'
        #self.stream.write(CLR.x)
        self.ERR = CLR.lr + 'Error: ' + CLR.x
        self.WARN = CLR.y + 'Warning: ' + CLR.x


    def __call__(self, *objs, **kwargs):
        stream = kwargs.get('stream', self.stream)
        self.blank.setdefault(stream, 0)
        for obj in objs:
            if hasattr(obj, 'reflow'):
                lines = obj.reflow(kwargs.get('width',0))
            else:
                lines = str(obj).split('\n')
            new_blank = 0
            for line in lines:
                line = line.rstrip()
                if not line and self.blank[stream]:
                    self.blank[stream] -= 1
                    continue
                self.blank[stream] = 0
                new_blank = 0 if line else new_blank + 1
                stream.write(line+'\n')
            self.blank[stream] += new_blank


    def print(self, *msg):
        self.stream.write(' '.join(map(str,msg)) + '\n')


    def pretty(self, v, expand=0, **kwargs):
        kwargs.setdefault('width', print.w)
        self('', Pretty(v, expand), '', **kwargs)


    def ln(self, *msg, **kwargs):
        self('', Text(*msg, **kwargs), '', **kwargs)


    def hr(self):
        self('━'*ConsoleBuffer.w)


    def progress(self, *msg, **kwargs):
        self('', Text(*msg))
        kwargs.setdefault('stream', self.stream)
        return ProgressBar(**kwargs)


    def box(self, *msg, **kwargs):
        self(*Box(*msg, **kwargs).reflow(kwargs.get('width',0), kwargs.get('height',0)))


    def ftr(self, *msg, **kwargs):
        txt = Text(*msg, **kwargs)
        if not txt: return self.hr()
        tbl = Table(0,-1,sides=0)
        b = Box(txt[:1], sides=7, **kwargs)
        bw = b.width()
        tbl('┯'+'━'*(bw-2)+'┯', '━'*(ConsoleBuffer.w-bw))
        tbl(b.reflow(), txt[1:])
        self(tbl, width=ConsoleBuffer.w)




class DocText():
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
        self.subs = []


    def parse(self, indent, i, lines):
        self.indent = indent
        sec = []
        while True:
            indent = (len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else self.indent) if i < len(lines) else -1
            if indent != self.indent or not lines[i].strip():
                if sec:
                    self.subs.append(self.sub_doc(sec))
                    sec = []
                if indent < self.indent:
                    return i, indent
                if indent > self.indent:
                    i, indent = self.subs[-1].parse(indent, i, lines)
                    i -= 1
            else:
                sec.append(lines[i].strip())
            i += 1
        

    def sub_doc(self, lines):
        kw = lines[0].lower() if len(lines) == 1 else ''
        if kw == 'parameters:': return DocParameters(dfn=self.dfn, text=Text(lines[0]))
        elif len(lines)==1 and lines[0].endswith(':') and not lines[0].endswith('::'): return DocSection(text=Text(lines[0]))
        return DocText(text=Text('\n'.join(lines)))
        
    
    def print(self, depth, stream=None):
        if hasattr(self, 'text'): 
            self.text.indent = '   '*depth
            print(self.text,'', stream=stream or sys.stdout)
        for s in self.subs:
            s.print(depth + 1, stream)

    def __str__(self):
        return (str(self.text) if hasattr(self, 'text') else '') + '\n'.join(map(str, self.subs))




class DocSection(DocText):
    def print(self, depth=0, stream=None):
        if stream: print.ln('**', self.text, '**', stream=stream)
        else: print.box(self.text)
        for s in self.subs:
            s.print(depth + 1, stream)




class DocParameterGroup(DocText):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.args = []
        
        try:
            p = self.text.split('|')
            assert(len(p) <= 2)
            p, self.explain = p if len(p)>1 else (p[0], '')
            self.explain = self.explain.strip()
            self.required = 'required' in self.explain
            for p in p.split(','):
                p = p.strip().split(' ')
                assert(len(p) <= 2), 'too many spaces %s'%p
                kv, typ = p if len(p)>1 else (p[0], '') if p[0].startswith('-') else ('-', p[0])
                kv2 = kv[2:] if kv.startswith('--') else kv[1:] if kv.startswith('-') else kv
                assert(not kv2 or kv2 not in self.dfn.doc_args), '%s in %s'%(kv2, self.dfn.doc_args)
                if kv2:
                    self.dfn.doc_args[kv2] = typ
                else:
                    self.dfn.doc_args[kv2] += 1
                self.args.append((kv, typ) if kv2 else (typ, ''))
        except Exception as e:
            print(e)
            self.dfn.error("Poorly formated parameter: ", self.text)
        
        
    def print(self, depth, stream=None):
        clrx, clrb, clra = ('','','') if stream else (CLR.x, CLR.b, CLR.lr if self.required else CLR.o)
        args = [clra + v[0] + clrx + (v[1] and ' '+v[1]) for v in self.args]
        expl = self.explain and clrb+' | '+self.explain+clrx
        print(('.. option:: ' if stream else '   '*depth) + ', '.join(args) + expl, stream=stream or sys.stdout)
        if stream: print('', stream=stream)
        for s in self.subs:
            s.print(depth + 1, stream)




class DocParameters(DocSection):
    def sub_doc(self, lines):
        return DocParameterGroup(dfn=self.dfn, text=lines[0])

    def print(self, depth=0, stream=None):
        if not stream: return super().print(depth)
        for s in self.subs:
            s.print(depth, stream)



def _pretty_obj(v, expand, width, depth):
    if not hasattr(v, '__pretty__'): return None
    return list(v.__pretty__().reflow(expand=expand, width=width, depth=depth))

def _pretty_dict(v, expand, width, depth):
    try:
        keymax = max(map(ConsoleBuffer.guessw, map(str, v.keys())))
        assert(not width or width-keymax > 30)
    except:
        return None
    clr = [CLR.y, CLR.c, CLR.m, CLR.g][depth%4]
    lines = []
    for k, v in v.items():
        k = str(k)
        for i, line in enumerate(Pretty(v).reflow(expand=expand, width=width and width-keymax-1, depth=depth+1)):
            prefix = ' '*(keymax+1) if i else ' '*(keymax-ConsoleBuffer.guessw(k))+clr+k+CLR.x+' '
            lines.append(f'{prefix}{line}')
    return lines

def _pretty_list(v, expand, width, depth):
    if isinstance(v, list) or isinstance(v, tuple):
        return _pretty_dict({f'[{i}]':val for i,val in enumerate(v)}, expand, width, depth)

def _pretty_flat(v, expand, width, depth):
    return list(Text((repr(v),)).reflow(width=width))


class Pretty():
    def __init__(self, value, expand=0):
        self.expand = expand
        self.value = value

    def __len__(self):
        return len(self.reflow())

    def width(self):
        return max(map(ConsoleBuffer.guessw, self.reflow()))

    def reflow(self, width=0, height=0, expand=0, depth=0, **kwargs):
        for fn in (_pretty_obj, _pretty_list, _pretty_dict, _pretty_flat):
            lines = fn(self.value, expand or self.expand, width, depth)
            if lines != None: break
        yield from lines[:height or len(lines)]
        if len(lines) < height: yield from ['']*(height-len(lines))
            
            

def exit(*parts, **kwargs):
    print.ln(*parts, **kwargs)
    sys.exit(kwargs.get('returncode',1))



def run(cmd, read=False, stderr='stdout', success=[0], silent=False, or_else=None, msg=True, err=True, stdin=None, env=None):
    cmd = cmd.split(' ') if isinstance(cmd, str) else list(map(str, cmd))
    if msg == None or msg == True: msg = Text('Running~lang ja~端末コマンドを実行する', '...')
    if silent: msg = None
    if msg: print.ln(msg, ['']*2, '   $ ', ' '.join(cmd))
    try:
        out = subprocess.PIPE if read else subprocess.DEVNULL if silent else None
        eout = {'stdout':subprocess.STDOUT, False:subprocess.DEVNULL, 'show':None}[stderr]
        resp = subprocess.Popen(cmd, stdout=out, stderr=eout, stdin=subprocess.PIPE if stdin else None, env=env)
        if stdin and not isinstance(stdin, bytes): stdin = stdin.encode('utf8')
        stdout = resp.communicate(input=stdin)[0]
    except Exception as e:
        resp = None
    if resp == None or success and resp.returncode not in success:
        if or_else != None: return or_else
        if err == False or err == '' or silent: raise RuntimeError(None if not resp else resp.returncode)
        if not msg: print.ln('   $ ', ' '.join(cmd))
        if read and resp:
            sys.stdout.buffer.write(stdout)
            sys.stdout.write('\n')
        if err == True:
            if not resp:
                err = Text(print.ERR, "{cmd} not found~lang ja~{cmd} のコマンドがない".format(cmd = cmd[0]))
            else:
                err = Text(print.ERR, "Command execution failed~lang ja~コマンドの実行に失敗しました", '  returncode: ', resp.returncode)
        raise UsageError(err)
    return stdout.decode('utf8') if read else True



def confirm(*text, **kwargs):
    success = kwargs.get('success', 'y')
    if input('\n'+'\n'.join(Text(*text, **kwargs).reflow())) != success:
        exit(kwargs.get('err', Text("Aborting~lang ja~実行中止")))



def _find_cmd(cmds, caller_fn):
    name = caller_fn.__name__
    while name[0] == '_': name = name[1:]
    for module_path, cmdmap in cmds.items():
        if caller_fn.__module__ != module_path: continue
        return cmdmap[name]



def short_cmd_list(docs):
    cmds = Table(2,0,-1, color1=CLR.y, border='')
    for doc in sorted(list(docs), key = lambda d: d.dfn.name):
        cmds('*', doc.dfn.name.replace('_','-'), DefaultCell(doc.subs[0].text) if doc.subs else '')
    if cmds:
        print(cmds, width=print.w)
        print.hr()



def _cli_run(caller_fn, args):
    if not isinstance(args, list): args = list(args)
    thd = current_thread()
    cmdref = _find_cmd(thd.cmds, caller_fn)
    if not cmdref.sub_module_paths:
        raise UsageError("You must configure the submodule path with @CLI(...) on the function that calls CLI.run(args).")
    subcmds = cmdref.sub_commands()
    if not subcmds:
        raise UsageError("@CLI%s was defined for '%s.%s' but it doesn't contain any commands marked with @CLI"%(cmdref.sub_module_paths, cmdref.module_path, cmdref.name))
    cmd = ('' if not args or args[0].startswith('-') else args.pop(0)).replace('-','_')
    allcmds = sorted(list(subcmds.keys()))
    suggestions = [x for x in allcmds if x.startswith(cmd)] if cmd else []
    if len(suggestions) != 1:
        short_cmd_list(subcmds[s].doc() for s in suggestions or allcmds)
        msg = [Text(''' Use `-h` or `--help` following the command to get more detailed help:
            ~lang ja~より詳細なヘルプを取得するには、コマンドの後に`-h`または` --help`を使用できる。''')]
        
        if suggestions and len(suggestions) < len(allcmds):
            msg = [Text(print.ERR, "Command '{cmd}' is ambiguous.~lang ja~「{cmd}」のコマンドが重複している。".format(cmd=cmd))]
        elif cmd:
            msg = [Text(print.ERR, "Unknown command '{cmd}'~lang ja~「{cmd}」のコマンドがない。".format(cmd=cmd))]
        else:
            msg = [Text(print.ERR, 'No command given.~lang ja~コマンドが指定されてない。')]
        msg += ['', Text('See above for a list of possible commands.~lang ja~コマンドについては、上記は参照のリストがある'), '']
        raise UsageError(*msg)
    cmd = subcmds[suggestions[0]](args)
    thd.stack.append(cmd)
    result = cmd.run()
    thd.stack.pop()
    return result



def _cli_main():
    return current_thread().stack[0].__class__


def _cli_remove_cmd(*args):
    cmds = current_thread().cmds
    for cmd in args:
        module_path, name = cmd.split('/')
        del cmds[module_path][name]


CLI.remove_cmd = _cli_remove_cmd
CLI.sub_cmd = _cli_run
CLI.main = _cli_main
CLI.args = {}
print = ConsoleBuffer(sys.stdout)


if __name__ == '__main__':
    print.set_stream(sys.stdout)
    thd = current_thread()
    thd.cmds = {}
    @CLI(*CLI_ENTRY_MODS)
    def cli(debug__g=False, info__i=False, en=False, ja=False, target__t='', *args):
        ''' This program controls the entire project.
        ~lang ja~このプログラムは、プロジェクト全体を制御します。
        
        Parameters:
            --target <str>, -t <str>
                Specify the target for configuration.  Targets are in ``config.py``, ``local_config.py``, ``vault/config.py``
                ~lang ja~ 構成のtargetを指定します。 ターゲットは ``config.py``, ``local_config.py``, ``vault/config.py``にある。

                See: :ref:`page_config`
            --en, --ja
                Show English/japanese documentation~lang ja~英語・日本語のドックス選択できる
            --info, -i, --debug, -g
                Run with info/debug level logging~lang ja~ 情報/デバッグレベルのログで実行
        '''
        import logging
        level = 'DEBUG' if debug__g else 'INFO' if info__i else os.environ.get(ENV_PREFIX+'LOGGING', 'WARN')
        os.environ[ENV_PREFIX+'LOGGING'] = level
        logging.basicConfig(style='{', format='{levelname:>7} {name:>10} {lineno:<3} | {message}', level=getattr(logging,level))
        print.set_doc_lang(en, ja)
        target = target__t or os.environ.get(ENV_PREFIX+'TARGET', 'local')
        from config import Config
        if target not in Config.all_targets():
            exit(print.ERR, "Invalid target '{t}'.  Must be one of:~lang ja~target「{t}」は無効。以下のように:".format(t=target),
                ['','']+['  '+t for t in Config.all_targets()])
        os.environ[ENV_PREFIX+'TARGET'] = target
        CLI.sub_cmd(cli, args)

    thd.cmds['__main__']['cli'].pos = [] # python 2.7 doesn't allow keyword only parameters, so fake it
    thd.stack = [thd.cmds['__main__']['cli'](args)]
    thd.cmds['__main__']['cli'].pos = ['debug__g', 'info__i', 'en', 'ja', 'target__t'] # Now that we have parsed we can put it back

    # Executing the virtual command root
    try:
        thd.stack[-1].run()
    except Exception as e:
        from cli import UsageError as UsageError2
        if not (isinstance(e,UsageError) or isinstance(e,UsageError2) or isinstance(e,AssertionError)) : raise e
        cmd = thd.stack[-1]
        if '' in cmd.vals:
            if len(thd.stack) == 1: print.set_doc_lang(cmd.vals['en'], cmd.vals['ja'])
            short_cmd_list(s.doc() for s in cmd.__class__.sub_commands().values())
            print('')
            cmd.__class__.doc().print(-1)
        else:	
            print('', *e.args)
            print('')
            sys.exit(1)
