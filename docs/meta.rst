===============
Meta
===============

The metadata is stored in a simple json format for maximum future compatibility.  



Blob
========

A blob is a 'large' chunk of opaque bytes.  i.e. image/video/audio data.

Typed Data
=============

This data can be reasoned about because it has a known type.  It is usually smaller in size than a blob.


File
==========

This is a file that exists in a normal inode filesystem.
Files can pop in and out of existence just like the working directory in a git repository.
A file could be generated simply from a `Blob` and a suitable filename.
Or, a more complex mapping, such as generating a json file from surrounding metadata, or creating an ID3 file from raw mp3 blob and artist metadata.



Storage
=========

The database objects must be physically stored on a real disk or in the cloud.  There are four types of storage.

 - Memory.  When loaded into memory the objects have a shape
 - inode-fS:  Data can be stored in normal files on a traditional filesystem.
 - custom-block:  Data can be stored direcltly on a block-device bypassing the filesystem overhead.
 - cloud:  This is similar to inode-fs but with different access constraints.

Ideally all of these methods should be interchangeable with only performance differences.
These different storage types are abstracted as just a 'stream'.  A stream has one or more 'URL's that can be used to access the stream.
For example, if you are on the same system as the Stream and it is an inode-file then you could just open the file and read it (maybe it is encrypted).
The URL might point to a cloud resource, or a resource on another machine via https, or another machine via webRTC SCP.
The access information for a Stream is context and user dependant.  Where your are and who you are changes what Stream URL's are available.

The speed, availability and ownership of the Streams is also important and specific to the accessor.

In order to assess data duplicity we need to know on how many unique DISKS the data resides on.  That precise information might disappear behind an abstract Stream URL.  For example when you put data in the cloud you have no idea on how many disks the data is spread, only a general reliability percentage.  For other, https based servers we can use a base url or subdomain to distinguish different disks.  Those 'disks' might be a hardware raid configuration in which case it just gets a higher reliability number.  A raided disk still has locality danger (house burning down).


Repository
----------

Connection
-----------

Depending on where/who you are, you have to get a connection to the repository before accessing any data.
For some repositories (local disk) this might be trivial, for other's (Friend's computer) it might be more tricky (waiting for their computer to turn on to access it via webRTC).  Other methods include https if a server is running and serving the repo.  Or ssh for harder to reach places.  Or maybe even a GUI for paper input.

Blob
--------

A list of all of the connection urls that represent the same chunk of data.
Any of the connection urls may be used to access the blob.
The blob's security/safety can be calculated.
Each connection has a last-used time so you can check-up on not frequently accessed connections.  Do you still know where that piece of paper is.  Was coffee spilled on it?

A blob is user-dependent (not all users can use the same connections).
A blob is device-dependant (not all devices can access every connection).

You start with a blob.  From analyzing each of the blobs connection URLs you can determine how safe/secure etc. this blob is.
You can also use one of the connections to stream the blob's data into memory(assuming you can also get the decryption key if the data is encrypted)






Log
========

The database is a log.  The log builds up the objects, their data, as well as the types of that data.

It is up to an interpreter program to read the log and derive useful data from it, as well as extending the log.
The log starts in a single storage unit, but it may branch out from there.



Data/code
===============

The static data and the code that interprets the data go hand in hand.
The data evolves forwards in time, but so does the code.
If you want to go back in time then you need to use the old code on the old data.
Even bugfixes should be dealt with carefully because the interpretation of old data might be dependent on the buggy code at the time.
Careful versioning is required for newer code to be used on older data (the converse is prohibited).
FYI.  Data types are more data, not code.



Platon
=========

A pure platonic idea.
    
Ok, they are just Objects as the programming world knows them.  So why invent a new word?
Because Objects are the physical manifestation of Platons, like a circle drawn on a piece of paper is the physical representation of a platonic circle.  But, yeah, a Platon is the abstract base class of an Object.


Namespace
-----------

Platons exist relative to a parent (namespace) platon in a DAG hierarchy as described by the `PlatonID`.

.. autoclass:: objfs.platon_id.PlatonID

A Platon might not actually know its own ID or its parent's.
The ID serves as a trail of information breadcrumbs that you can follow to find the identified platon.
So a parent must be able to use one (or more) of the ID crumbs to find the next parent in the chain.

It is common in programming to bring objects in from another namespace.
There is the possibility of a collision so there needs to be a translation table to map the colliding ID to a new ID.
Similarly, the translation table can map different IDs that are actually the same platon.

Relationships
---------------

The most important part of the entire database is describing how different platons relate to each other.

Relationships are a 3-tuple (from, to, kind) that define a direction (from→to) and the kind of relationship.
When all pieces of the tuple are given then the relationship is explicit.
Other, implicit, relationships exist where some discovery computation (of varying difficulty) is required.

 - (from, ?, 'owner') Who are my children?
 - (?, to, 'owner') Who is my owner?
 - (from, to, ?) What are all the different kinds of relationships between these two?

It is an implementation detail how the actual relationships are stored.

Given the method of identifying platons, we already have a DAG of relationships.
These relationships are of the `Ownership` kind.


Type
========

Platons can be associated with a Type.
A type association tells you what other associations you can expect from this Platon.

Platon#123 is associated with the name "Jim".
Platon#123 is associated with the type Person.  Being a person means you can expect to have a name association.
#123 is also associated with the type TeamMember.  TeamMember's have a name.
These two types both demand that Platon#123 have a name.  They both share the name, not duplicate it as a piece of sub-data beneath their type.

But maybe the two types are in conflict.  Maybe the TeamMember's name refers to their role in the team or jersy number.
To handle conflicting names we can scope the jersey number with the TeamMember TypeID.

When you lookup associated data, you do so in the context of a Type.
So from the TeamMember's perspective, the scoped name (jersey number) would be found before the name "Jim".

Normally a Data structure defines field names.

.. person:

.. code-block::

    class Person:
        name
        birthdate

But what if you put a date in the 'name' field?  Ah, lets give the fields types so that we put the correct data in there.

.. code-block::

    class Person:
        name :String
        birthdate :UnixTimestamp

    Person(name="1980-1-1", birthdate=1e100)

Hmmm, that didn't work.  Even if you played by the rules, the value "Jim" when copied out from the Person.name field loses its meaning (that of being a name).

.. code-block::

    class Person:
        name :Name
        birthdate :Birthdate

Now we have moved the full meaning to the data itself.  So why do we need the field names any more?  They carry no important semantic information (because we moved that information to the type).

.. code-block::

    class Person:
        :Name
        :Birthdate

Now, instead of asking for Person.name, you ask for the value associated with the person that has the type Name.
The type (Person) tells you what types of Platons you *expect* to find associated with the Platon typed Person.  It is just an expectation, the system is flexible enough to break the rules.

There is no ordering to the associations.  If a `Person` has multiple `Name` objects associated with it and you want to keep them ordered (in preference order, for example, or alphabetical order), then you need to to sort them by yourself.  You might need to associate some kind of key such as 'preference' so that you can sort by that key.


.. blob:

Blob
=============

At some point ideas are not platonic any more and you need real data.

The string "Jim" is real data that needs to be associated as the 'name' of Platon#123.
By itself, the string "Jim" isn't a 'name', it is just a sequence of three unicode characters.

`Blob`\s are `Platon`\s that have an opaque list of bytes associated with them.
Those Blobs can get Type associations such as 'utf-8' or 'mp3'.  They can have multiple Types (utf-8, Name).


Meta-classes
=============

`Platon` and `Blob` are types that exist in the meta-realm of the code that interprets the data.
You have a chicken and egg problem trying to define a Platon in terms of a Platon.



