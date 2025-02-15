=========
Theory
=========




Object ID.   If an object does not have an ID then it has no way of being distinct.
How do you refer to one object and not another?
It could be an opaque string of bits.  But how many bits are necessary?  Do you just choose many bits (256?) in a flat namespace and say the odds of collision are low?  Or is it better to layer information/structure known about the object into the ID so that fewer bits are needed to eliminate name collisions.

The ID is a very absolute way of identifying the object.  Identification may be context dependant, such as how everyone can use 'mom' and 'dad'.  In that case there must be some verbage that equates different IDs.

One of the more important relationships between objects is one of parent/child ownership, where a child has a single parent owner.
An object may be in multiple DAG relationships like that.  If one is picked (which one?) then it can be layered on top of the ID.






Your data is stored in various locations on various types of media.  On paper, on a friend's USB stick, in a folder in an ext4 filesystem, on a dedicated filesystem.


We are reinventing language for describing ides.

A platon is a pure raw idea, initially unencumbered by any meaning.
We build up a picture about that platon's meaning by talking about it using other platon's.

Eventually we give up and just describe it in English.

So the trade off is the expressivity of the language, and the mechanistic query-ability.

We adopt the lisp sentence structure (verb, subject, objectA, objectB, ...).

The terms may be an object id (possibly relative to a different object), or raw data bytes


Where subjects, verbs, and objects are just platons.  Their interpretation in each of the sentence roles is defined in the meta-information layer (English documentation).



Here is a list of example, well-known, platons:

- Human
- Einstein
- Integer
- UTF8

If a platon lives 'within' another platon then that parent acts as a natural namespace.
An object's ID is a sequence of bits of info such that if you follow the bread crumbs, you will find the the object.
That means the the object is in a fixed spot.  We don't have multiple owners fighting for ownership of an object.
The disadvantage of that model is that it is difficult to move the object.  Moving the object means the ID changes, so
you have to notify everyone of the move.  That doesn't feel unnatural, however.
For data that doesn't have a clear owner it makes sense to put it in a high, stable, namespace.
Movement also shares the same problem of deletion.  A move is a delete followed by a create.  We want to handle deletions, so we will also be able to handle moves.


Lists and dictionaries are the same.  They are both just a namespace.  In a 'List' the sub-id's are expected to be contiguous starting at 0.

Lets say we have a `Circle` instance.  We expect it to have a radius.  We could say that any circle instance has its radius stored in the ID#1 slot.  We would be able to find the radius that way.  But that is very inflexible.  What if we instead want to specify the diameter, or what if the circle doesn't own the radius variable.  That is why we don't overload the ID with extra meta-data.











PLATO FS ship of thesus


large data chunks (image sensor data, text body) are immutable stored separatly from metadata in linear (not deleteable) fashion on an a block device directly without a 'filesystem'

modern files are handicapped trying to do too many and too few things at once.
  - What is the filename of an image?  John-birthday-2025.jpg ??  Trying to put metadata into that constrained file system.
  - audio/image container formats.  Storing image size, sensor data, gps coordinats, memo, artist, genera.

git maintains a local working set as a snapshot of the 'real' tree of objects.
We can checkout (mount) a unix-fs (inodes) of a slice of the plato-fs:   mount /pics "Aaron and Mei last fall"
Traditional programs can interact with that fs (via the OS <stdio.h>).  File creation inside that virtual-fs sends the new plato-file to a triage area where it can be properly incorperated into the plato-fs
Like git, the local working directory can be checked against the repository to see if the files are in the repo or not.


the metadata is of course real data that needs to be stored on disk.  chicken and egg problem.
For some objects the data is the primary size (videos).  Other objects may be mostly, or purely, metadata.
The metadata/blob data distinction fades.

The object needs to be in various indexes.

A 'folder' is just an object.

blob data has ownership/control issues.
You can have the blob on your disk in your room.
Or you can have contractual control over it (cloud services).
Or you can have no control over it (Someone else's data).


Sending someone a message (email, x, gchat, line, ...) is creating an object with a (probably) small associated blob of data (message text) and then sharing that object with someone else.
They may just keep the data on your computer and view it (no control) or they may want to take control over it (copy it to their computer).


Two different people may have a converging/diverging history over a single object.
Bob takes a picture and shares it with Sally.  Sally adds a comment that is shared back to Bob.
The single (shared) object is consistent between them.  Sally shares the object with Jim.
Jim makes a snarky comment about Bob to Sally.
Now the object has diverged and Bob has a different view of it (sans Jim's comment) even though it is the same object (same ID).
When Sally shares her changes with Bob the changes need to get merged together or the object could be split into a new unique object


So what is an object?  An object is a set of references to other objects plus a (possibly empty) list of immutable opaque blobs of bytes.

An object can be a member of sets.  The sets can imbue meaning and attributes to the object.
The sets also provide the meta-information about what the references 'mean'.  A reference has two objects associated with it, the 'type' and the 'value'.  For example, 'height' and '32'  Where 'height' comes from the 'sized' set object.

If you are in the 'commentable' set then your object might have a reference to a comments object.
You can be in other, purely organizational sets.
Implicit sets (between certain date ranges)?


Transactional changes to the filesystem alter possibly multiple object's references / blobs at once.

Like git, a repository is an independent collections of objects.  A single user has write control over a repository.
A different user will have their own unique repository.  the two users may share every object with each other so there will be no duplicated data if they reside on the same system.


A Host hosts one or more universes.
A Universe is a collection of objects and blob data stored on disks.
A Disk is a unique physical device storing data.
A World is a subset of a Universes's objects that is owned by a single user.

Two users can share objects between their worlds.
The object's identity will be maintained across worlds even if the specific properties are different.  You can have an object that looks blue on one world but yellow in another even with the understanding that it is the same object.
If the object is not in your universe then you don't have control over it.  It may disappear if the real owner deletes it.
If it is important to you then make sure to copy it to a universe under your control

An object is a uniqueID.  Various views (classes) are layered onto the object.  Those views can be shared (in whole) with other users.





