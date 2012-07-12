#!/usr/bin/python
#

"""
Implementation of the common "Manhattan distance" problem. On a grid, the
Manhattan distance between two points is the distance along those streets, i.e.
the distance in blocks. For example, if point A is three blocks west and five
south of point B, their Manhattan distance is eight blocks.

The interview question is, given two points with a manhattan distance of n + m,
how *many* paths of that manhattan distance are there between the points?

Here are a couple implementations, the recursive solution and the closed-form
solution n + m choose m.
"""

def main():
    functions = [recursive, closed_form]
    print ['n', 'm'], ['recursive', 'closed form']
    
#    for n, m in [(0, 0), (1, 0), (1, 2), (2, 3), (2, 5), (4, 8), (6, 13)]:
    for n in range(0, 9):
      for m in range(0, 9):
        counts = [fn(n, m) for fn in functions]
        print [n, m], counts

        # they should all get the same answer
        assert counts.count(counts[0]) == len(counts)
    # end for


def recursive(n, m):
    """ Finds the number of paths between two points with manhattan distance
    n + m. The implementation is recursive and fairly elegant.
    """
    assert n >= 0 and m >= 0
    
    if n == 0 or m == 0:
        return 1
    else:
        return recursive(n - 1, m) + recursive(n, m - 1)


def closed_form(n, m):
    """ Finds the number of paths between two points with manhattan distance
    n + m. The implementation is the closed form solution, n + m choose m.
    """
    return factorial(n + m) / (factorial(n) * factorial(m))
    


def factorial(x):
    """ Returns the factorial of x.
    """
    assert x >= 0
    if x == 0:
        return 1
    else:
        return x * factorial(x - 1)
    

if __name__ == '__main__':
    main()
