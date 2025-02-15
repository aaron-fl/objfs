from .git import Git
from cli import CLI

@CLI('.git.git_cmds')
def git(*args, repository__C='.'):
    ''' Run meta-git commands

    Parameters:
        --repository [repo], -C [repo]
            Path to repository, or name of repository.  Can be specified multiple times.
    '''
    return CLI.sub_cmd(git, (args[0], repository__C, *args[1:]) if args else [])
    
