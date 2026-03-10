from itertools import islice
from typing import Iterable, Iterator, Tuple, TypeVar

T = TypeVar("T")

def batched(iterable: Iterable[T], n: int) -> Iterator[Tuple[T, ...]]:
    """
    Batch data into tuples of length n. The last batch may be shorter.
    
    Example:
        list(batched('ABCDEFG', 3)) --> [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]
    """
    if n < 1:
        raise ValueError("n must be at least one")
        
    iterator = iter(iterable)
    while True:
        batch = tuple(islice(iterator, n))
        if not batch:
            break
        yield batch
