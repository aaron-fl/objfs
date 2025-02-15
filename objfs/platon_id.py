

class PlatonID():
    ''' A binary ID to uniquely identify `Platon`\\s

    Like file system path names Platons have an ID as well as full path.
    The ID size is a multiple of a byte.  The IDs self-describe their length.

    ========= =============== ==========
    Bits      Description     Unique IDs
    ========= =============== ==========
    0000 0000 NULL            1
    0xxx xxxx 1byte (7bit)    125
    0111 1110 current ./      1
    0111 1111 parent ../      1
    100x xx.. 2byte (13bit)   8192
    101x xx.. 4byte (29bit)   536 M
    110x xx.. 8byte (61bit)   2.3e18
    1110 xx.. 16byte (124bit) 2.13e37
    1111 ???? reserved
    ========= =============== ==========
    '''

    __slots__ = 'id',

    NULL = bytes([0])
    PARENT = bytes([127])
    CURRENT = bytes([126])

    @staticmethod
    def size(bytes):
        if not bytes[0] & 0x80: return 1
        if s := (((bytes[0]>>5) + 1) << 1) & 0x7: return s
        return 8 if bytes[0]>>4 == 0xe else 0


    @staticmethod
    def verify(id):
        if len(id) != PlatonID.size(id): raise ValueError(f'Invalid ID: {id.hex()}')
        return id


    @staticmethod
    def from_hex(hex):
        if hex == '.': return PlatonID.CURRENT
        if hex == '..': return PlatonID.PARENT
        if not hex: return PlatonID.NULL
        if len(hex)%2: hex = '0'+hex        
        return PlatonID.verify(bytes.fromhex(hex))

    
    @staticmethod
    def from_int(idx):
        if idx < 125: return bytes([idx+1])
        if idx < 0x2000 + 125: return ((idx-125)|0x8000).to_bytes(2,'big')
        if idx < 0x20000000 + 0x2000 + 125: return ((idx-125-0x20000)|0xa0000000).to_bytes(4,'big')
        raise NotImplementedError()


    @staticmethod
    def to_int(part):
        if p := {PlatonID.NULL:-1, PlatonID.PARENT:-2, PlatonID.CURRENT:-3}.get(part, None):
            return p
        size = PlatonID.size(part)
        if size == 1: return part[0]-1
        if size == 2: return (int.from_bytes(part,'big')&0x1fff) + 125
        if size == 4: return (int.from_bytes(part,'big')&0x1fffffff) + 0x2000 + 125
        raise NotImplementedError()


    @staticmethod
    def each_part(id):
        i = 0
        while i < len(id):
            s = PlatonID.size(id[i:])
            yield id[i:i+s]
            i += s


    def __init__(self, *parts):
        ids = []
        for part in parts:
            if isinstance(part, int):
                ids.append(PlatonID.from_int(part))
            elif isinstance(part, PlatonID):
                ids.extend(part.parts())
            elif isinstance(part, (bytes, bytearray)):
                ids.extend(PlatonID.verify(b) for b in PlatonID.each_part(part))
            elif part == None:
                ids.append(PlatonID.NULL)
            else:
                ids.extend(PlatonID.from_hex(s) for s in str(part).split('_'))
        if not ids or len(ids) == 1 and ids[0] == PlatonID.NULL:
            self.id = PlatonID.NULL
        else:
            # Collapse .. and .
            i = 0
            while i < len(ids)-1:
                if ids[i] == PlatonID.NULL: raise ValueError(f"No NULL allowed in a PlatonID path")
                if ids[i] == PlatonID.CURRENT:
                    ids[i:i+1] = []
                    continue
                if ids[i] != PlatonID.PARENT and ids[i+1] == PlatonID.PARENT:
                    ids[i:i+2] = []
                    if i: i -= 1
                    continue
                i += 1
            if not ids: ids = [PlatonID.CURRENT]
            self.id = reduce(lambda a,b: a+b, ids)
            

    def __str__(self):
        return '_'.join(self.hex_parts())


    def __repr__(self):
        return f"PlatonID('{self}')"


    def __hash__(self):
        return hash(self.id)


    def __eq__(self, other):
        if not isinstance(other, PlatonID): other = PlatonID(other)
        return self.id == other.id


    def __truediv__(self, other):
        return PlatonID(self, other)


    def split(self):
        s = PlatonID.size(self.id)
        return PlatonID.to_int(self.id[:s]), PlatonID(self.id[s:])


    def parts(self):
        return PlatonID.each_part(self.id)


    def hex_parts(self):
        for part in self.parts():
            if part == PlatonID.CURRENT: yield '.'
            elif part == PlatonID.PARENT: yield '..'
            else: yield hex(int(part.hex(),16))[2:]


from functools import reduce
