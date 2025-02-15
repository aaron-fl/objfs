from cli import CLI, run, print, CLR, Text
import yaml, os.path, shutil, os


def _find_section(section):
    docs = os.path.realpath('docs/html')
    for base, dirs, files in os.walk(docs):
        for f in files:
            if f.lower() == section.lower()+'.html':
                return os.path.join(base, f)
    return os.path.join(docs, 'README.html')



def open_docs(section):
    import webbrowser
    url = 'file://' + _find_section(section)
    print.ln(f'Opening documentation in the browser~lang ja~ブラウザでドキュメントを開く', '...', ['']*2, url)
    try: run(['open', '-a', 'Google Chrome', url])
    except:
        try: run(['open', '-a', 'Safari', url])
        except:
            webbrowser.open(url, new=2)



def cli_gen(outfolder):
    #os.makedirs(outfolder)
    main = CLI.main()
    print.ln("Generate cli.py documentation~lang ja~cli.pyドキュメントを生成する")
    create_file(main, outfolder, prefix=[main.name])



def build_graphs(dot):
    graphs = []
    for base, dirs, files in os.walk('docs'):
        for f in filter(lambda x: x.endswith('.dot'), files):
            outname = os.path.splitext(f)[0]
            if dot and dot != 'all' and dot != outname: continue
            graphs.append((os.path.join(base, f'{outname}.png'), os.path.join(base,f)))
    if not graphs: return
    try:
        run('dot -V', msg='', err=Text(print.WARN, '''
            Graphviz not installed.  Not building graphs.
            ~lang ja~Graphvizがインストールされていません。 グラフを作成しない''', 
            ['\n'], '   $ brew install graphviz'))
    except Exception as e:
        print(*e.args)
        return

    gph = print.progress('Building graphs', '...', steps=len(graphs))
    for fout, fin in graphs:
        gph.step(fin)
        run(['neato', '-T', 'png', '-o', fout, fin], msg='')
    gph.done(f'Built {len(graphs)} graphs')




def push_docs(remote):
    run('git -C docs add -A')
    run(['git', '-C', 'docs', 'commit', '--amend', '-m', 'cli.py docs build'])
    run(['git', '-C', 'docs', 'push', remote, '--force', 'HEAD:docs'])




def write_cmd(cmd, f, prefix=[]):
    if not cmd.sub_module_paths: f.write(f".. _{'_'.join(prefix)}:\n\n")
    f.write(f"{cmd.name.replace('_','-')}\n{'-'*len(cmd.name)}\n\n")
    cmd.doc().print(-1, stream=f)
    if cmd.sub_module_paths:
        f.write(f".. toctree::\n   :maxdepth: 1\n\n   {'_'.join(prefix)}\n\n")
        f.write('.. list-table::\n   :widths: 1 100\n\n')
        for sub in cmd.sub_commands().values():
            f.write(f"   * - :ref:`{'_'.join(prefix)}_{sub.name}`\n")
            f.write(f"     - " + str(sub.doc().subs[0].text) + '\n')
        f.write('\n')
        #f.write(f".. toctree::\n   :maxdepth: 2\n\n   {'_'.join(prefix)}\n\n")




def create_file(cmd, outfolder, prefix=[]):
    fname = os.path.join(outfolder, f"{'_'.join(prefix)}.rst")
    print(f"  {fname}")
    os.makedirs(os.path.split(fname)[0], exist_ok=True)
    with open(fname, 'w') as f:
        f.write(f".. _{'_'.join(prefix)}:\n\n")
        f.write(f"{'#'*len(cmd.name)}\n{cmd.name.replace('_','-')}\n{'#'*len(cmd.name)}\n\n")
        cmd.doc().print(-1, stream=f)
        f.write(".. contents::\n   :local:\n\n")
        subs = cmd.sub_commands()
        for name in sorted(subs):
            write_cmd(subs[name], f, prefix + [name])
            if subs[name].sub_module_paths: create_file(subs[name], outfolder, prefix + [name])
