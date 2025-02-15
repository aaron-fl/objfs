from cli import CLI

@CLI('.docs.docs')
def docs(*args):
    ''' View/build documentation
    '''
    if not args: args = ['view']
    return CLI.sub_cmd(docs, args)
    
