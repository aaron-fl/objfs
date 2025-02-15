


class HasFields():
    REQ = object()

    def __init__(self, **kwargs):
        for k, v in self.fields.items():
            if k in kwargs: v = kwargs.pop(k)
            if v == HasFields.REQ: raise ValueError(f"Parameter {k!r} is required")
            setattr(self, k, v)
        if kwargs: raise ValueError(f"Invalid: {kwargs}")
    

    def __repr__(self):
        args = []
        for k in self.fields:
            try:
                v = getattr(self, '__repr__'+k)()
            except:
                v = getattr(self, k)
            if v == self.fields[k]: continue
            args.append(f"{k}={v!r}")
        return f"{self.__class__.__name__}({', '.join(args)})"



class StorageLocation(HasFields):
    ''' This is a physical location in the world.
    Physical location is a factor in security and reliability of the data stored there.
    Two different media in the same location may die together in the same fire or power supply explosion.

    More abstract locations such as cloud providers where data is RAIDed across multiple disks and regions will also be represented by a `StorageLocation` object.

    Keyword arguments:
        - id (alpha-num)
        - name (human readable)
        - memo (more information)
        - location (StorageLocation)
        - failure_rate (how likely is data loss at this location)
        - security (Who has access to this location, how difficult is it for someone else to physically access this location)
        - owner (related to security) Who actually owns this location?  Cloud provider?  Your home?  Friend's home?  If your data is not in a location that you own, then it isn't your data.  However, it is fine to store encrypted data in a location that you don't own as a backup (or if you don't really care about the data (a picture they shared with you))
        
    Examples:
        - bedroom vault
        - nuclear silo
        - home pc
        - GCS (asia-north)
    '''

    fields = dict(id=HasFields.REQ, name=HasFields.REQ, memo='', location=None, failure_rate=0, security=None)

    def full_name(self):
        if self.location: return self.name + ', ' + self.location.full_name()
        return self.name
        
    def __str__(self):
        return f"{self.full_name()} (id:{self.id})\n{self.memo}"



class Storage(HasFields):
    ''' This is where the bits actually reside.

    Keyword arguments:
        - id (alpha-num)
        - name (human readable)
        - memo (more information)
        - kind (disk, ssd, paper, ...)
        - failure_rate (how likely is data loss)
        - aging_rate (how does the failure rate age over time)
        - speed (read, write, spin-up)
        - cost
        - size (size in bytes)
        - location (StorageLocation)

    Examples:
        - disk
        - ssd
        - paper
        - brain
    '''
    fields = dict(id=HasFields.REQ, name=HasFields.REQ, memo='', kind=None, failure_rate=0, aging_rate=0, speed=None, cost=None, size=None, location=None)

    def __str__(self):
        s = f"{self.name} (id:{self.id})"
        if self.location:
            s += f"\nLocated {self.location.full_name()}"
        if self.memo:
            s += f"\n\n{self.memo}"
        return s



class KVStore(HasFields):
    ''' A key-value store of data that lives in a `Storage`.

    The keys are arbitrary ID values (maybe a pathname).  The values are opaque blobs of data.
    
    The owner(s) of the KVStore is ultimately determined by the owner(s) of the `StorageLocation`.

    Keyword arguments:
        - id
        - name
        - base (some kind of offset within the `Storage`)
        - encryption (How are the values encrypted?)
    '''

    fields = dict(id=HasFields.REQ, name='', storage=None, base=None, encryption=None)



class Blob():
    ''' A blob is a chunk of data that is stored in one or more `KVStore`_s.

    The Blob keeps track of all the different KVStores that hold copies of the blob's data.
    Given the particular execution environment there may or may not be an available Bridge to the different `KVStore`_s.

    Last access information also should be kept for each KVStore so that health-checkups can be done.
    If one KVStore goes up in flames, how and when would you find out?
    But this is outside the scope of the Blob object.
    '''

    def __init__(self, *, bridges, stores=None,data=None, id=None):
        ''' Parameters:
            data :bytes
                The actual data of the blob.
            stores :[(kvstore_id, key)]
                The kvstore_id is used to select the `Bridge` to use.
                The key is for the value within that `KVStore`.
            bridges :{kvstore_id:[Bridge]} 
                A dictionary of `Bridge`_s for resolving the stores
        '''
        self.stores = stores or []
        self.bridges = bridges
        self.data = data

