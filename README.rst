===============
Object FS
===============

About
======

This solves these related problems in the most simple way possible.

 - Object filesystem

   It is hard to associate metadata with files.  You have the filename and the folder that you put it in (path).
   Some file formats also try to accommodate metadata (poorly) (ID3, EXIF).
   But what if you want to associate arbitrary metadata (comment, etc.) with a .txt file or other arbitrary file?

   Often we embed a database into the filesystem (sqlite) so that we can model our application's data better.
   What if the base filesystem was simply much better at representing data and their relationship with other data.

 - Data backups
   
   We never want our precious puppy pics to be lost to the sands of time.
   The cloud is the defacto place for backups and fault-tolerant storage.  But what about data ownership?
   Any data that gets stored in the fault-tolerant cloud needs to be encrypted (by us) so that it isn't used without our permission.
   In addition, we need our bytes on media that we are in physical possession of.  True ownership, not contractual ownership.
   Some data (like encryption keys) are so important that they should be stored in physical (paper) form.

 - File sharing

   How do you share a picture with friends and family.  Along with a caption describing the picture.
   Oh yeah, It would be nice if they could leave their comments too...

   What started off as file sharing turned into object sharing (for comments and other metadata).
   Since we know now to do data backups, we can treat our friend's computer as a place where our shared picture
   is backed up.  Or similarly, from their perspective the picture is backed up on our computer.
   If they don't want to take more control over it (by replicating it to a drive that they own) then it can just stay there.

 - Single filesystem

   This is related to backups and sharing.  We have files scattered across multiple computers / phones.
   They should all be able to access every file.  There should be only 'one' file, even though there are multiple copies of it on the different devices.

 - Git-like versioning/history

   Checkout a working tree, modify it, check it back in.  Check out an old version, view it, delete the working tree.
   Data should never actually get deleted in a world with infinite storage.
   Archive it, sure, but never delete it forever.


.. code-block:: console

   $ ./cli.py docs

https://github.com/aaron-fl/objfs/blob/docs/markdown/README.md


Objectives
=============

 - speed:  Slow is fine.  This is not a high-throughput transactional db for short-lived constantly mutating state.
 - flexibility:  The database should be maximally flexible, greater than or equal to python
 - multi-user:  Objects in the database can be shared r/rw with multiple users
 - multi-access:  Simple full-database mutex is ok to start...
 - robust: Data should be stored across many disks and cloud.  In normal files and in special-purpose block-device space
 - git-shareable:  Sharing is git-like where you try to synchronize your database with other devices/users.
 - no-delete:  Deleting data is dangerous and mostly pointless when storage is so cheap.  Archive it, don't delete it.
 - history: similar to the no-delete principle and git repositories the whole history of changes should be kept.


cli.py
=========

`cli.py <cli>`

.. toctree::
   :maxdepth: 2

   docs/gen/cli/cli
   docs/config
   docs/theory


Tests
========

.. code-block:: console

   $ ./cli.py -t test test


Meta
========

.. toctree::

   docs/meta


.. toctree::
   :caption: Indexes

   genindex
   modindex
   search
