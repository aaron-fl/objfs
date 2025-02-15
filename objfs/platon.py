
def platon_graph(*roots):
    lines = ['digraph {','fontname="Helvetica";', 'node [shape=rectangle];',]
    seen = set()
    def _add_node(node):
        if node in seen: return
        seen.add(node)
        lines.append(f'n{id(node)} [label=<{node.gviz_label()}>];')
        for fwd in node.fwd:
            _add_node(fwd)
            lines.append(f'n{id(node)} -> n{id(fwd)};')
            print(f"Edge n{id(node)} ({node!r}) -> n{id(fwd)} ({fwd!r})")
    for node in roots: _add_node(node)
    return lines + ['}']

    

class Platon():
    ''' An abstract base class describing what abilities a platon is expected to have.
    '''
    def __init__(self):
        self.namespace = {}
        self.sentences = {}


    def __str__(self):
        ''' This will return the default `Name`
        '''
        #for prop in self.each(Property):
            
        return str(self.name())


    def __repr__(self):
        ''' This will return a debugging-level view of the platon
        '''
        return f"{self.__class__.__name__}#{hex(id(self))[2:]}"


    def lookup(self, id):
        ''' Given an `PlatonID` you should be able to return a `Platon` object.
        '''
        if id == PlatonID.CURRENT: return self
        key, next_id = id.split()
        if key == -1: next = None
        elif key == -2: next = self.parent_namespace()
        elif key == -3: next = self
        else: next = self.namespace.get(id)
        if next == None: raise KeyError(f'Platon:{id} was not found in {self!r}')
        return next if next_id == '0' else next.lookup(next_id)


    def define(self, verb, *objects):
        ''' Define a new sentence with this platon as the subject.
        '''
        self.sentences.setdefault(verb,set())
        self.sentences[verb].add(objects)


    def parent_namespace(self):
        ''' Return the parent platon in the namespace hierarchy.
        This might be computationally expensive
        '''
        raise NotImplementedError()


    def __iter__(self):
        ''' Yield every sentence (verb, *objects)
        '''
        for verb, objects in self.sentences.items():
            for objs in objects:
                yield (verb, *objs)
    

    def each(self, verb):
        ''' Yield every sentence from the given verb
        '''
        yield from self.sentences.get(verb, [])


    #def gviz_label(self):
    #    return f'<font point-size="12" color="gray">{html.escape(str(self.id))}</font><br/><font point-size="14">{html.escape(str(self))}</font>'



class Blob(Platon):
    def __init__(self, *id, kvs=None, data=None):
        super().__init__(*id)
        self.data = data or self.load_from_kvs(kvs)

    def load_from_kvs(self, kvs):
        if not self.kvs: return b''
        # Load from one of the kvstores
        raise NotImplementedError()


    def __str__(self):
        name = self.name()
        if name != None: return str(name)
        if UTF8 in self.fwd:
            data = self.data.decode('utf8')
        else:
            data = '0x' + self.data.hex()
        return data

    def __repr__(self):
        return f"Blob({self.id}, {self})"

    def gviz_label(self):
        return f'<font point-size="12" color="blue">{html.escape(str(self.id))}</font><br/><font point-size="14">{html.escape(str(self))}</font>'


from functools import reduce
import html


def named(txt):
    return Blob(1, data=txt.encode('utf8')).refs(UTF8, Name)


#Property = Platon(b'\xb0\x00\x00\x01')

#def isa(subs):
#    return 

#Owner = Plato
#Name = Platon(b'\xb0\x00\x00\x01')
#String = Platon(b'\xb0\x00\x00\x02')
#UTF8 = Platon(b'\xb0\x00\x00\x03')
#ASCII = Platon(b'\xb0\x00\x00\x04')
#ISA = Platon(b'\xb0\x00\x00\x05')

#String.refs(named('String'))
#UTF8.refs(named('UTF8'))#isa(String))
#Name.refs(named('Name'))
#ASCII.refs(named('ASCII'))#, isa(UTF8))


#Comment = Platon(b'\xb0\x00\x00\x05').refs(named('Comment'))
