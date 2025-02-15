
import sys, logging
from subprocess import Popen, PIPE, DEVNULL
from config import Config
from cli import CLI, CLR, print

log = logging.getLogger('grep')

def grep_group_cmds(groups, pattern, *args):
    base = ['grep'] + list(args)
    for mod, locs in groups.items():
        for loc in locs:
            if loc[0]:
                exclude = [f'--exclude={e}' for e in loc[2:]]
                include = [f'--include=*.{e.strip()}' for e in loc[0].split(',') if e.strip()]
                cmd = base + include + exclude + ['-r', pattern, loc[1]]
            else:
                cmd = base + [pattern] + list(loc[1:]) + ['/dev/null']
            log.debug(' '.join(cmd))
            yield mod, cmd



def grep_groups(groups, pattern, *args):
    g = {}
    for m, p in [(m, Popen(cmd, stderr=DEVNULL, stdout=PIPE)) for m, cmd in grep_group_cmds(groups, pattern, *args)]:
        g.setdefault(m,'')
        g[m] += p.communicate()[0].decode('utf8')
    return g



def grep_files(files, pattern, *args):
    if not files: return ''
    cmd = ['grep', '--color=never'] + list(args) + [pattern] + files
    log.debug(f"Grep files: {' '.join(cmd)}")
    return Popen(cmd, stderr=DEVNULL, stdout=PIPE).communicate()[0].decode('utf8')



@CLI()
def grep(pattern, *, case__c=False, group__g=[]):
    ''' Grep all relevent files (and filenames) in the project for regex <pattern>

    Parameters:
        <str>, --pattern <str>
            A regex pattern to search for
        --case, -c
            Case sensitive search
        --group [grp], -g [grp]
            Only show matches in specific groups
    '''
    groups = Config().grep_groups
    group__g = group__g or groups.keys()
    groups = {k:v for k,v in groups.items() if k in group__g}

    args = ['-n', '--color=always']
    if not case__c: args += ['-i']
    matches = False
    print('')
    for m, stdout in grep_groups(groups, pattern, *args).items():
        if stdout:
            matches = True
            sys.stdout.write(stdout)
            print.ftr(CLR.g, m, CLR.x)
    if not matches: print.ln(print.WARN, "No matches found~lang ja~見つからなかった")
