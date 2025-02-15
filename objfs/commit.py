from .kvfs import Blob

class Commit(Blob):
    ''' A Commit is the same as git. It stores a reference to its predecessor commit and changes some stuff atomically.

    A commit can be shared with other users.


    A1: a <- b <- c <- d
    A1B1 : (s) <- (u)

    A2: c <- d0 <- e0

    A3: c <- d1 <- d1

    B1-A: x <- y <- z
    B1: q <- r <- s:a,c <- t <- u:a


    Many objects are disjoint.  Applying an artificial ordering to them is unnecessary.
    Other mutations mutate a specific version.


    '''