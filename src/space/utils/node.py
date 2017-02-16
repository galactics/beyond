#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module helps to find the shortest path between two element in a
hierarchy or in a graph.
"""

from collections import OrderedDict


def _merge(x, y):
    """Remove commons ancestors and concatenate two passes

    Args:
        x (list)
        y (list)
    Returns:
        list
    """

    shortest, longuest = sorted((x, y), key=len)
    for _ in range(-len(shortest), 0):
        if shortest[-1] == longuest[-1]:
            try:
                if longuest[-2] == shortest[-2]:
                    longuest.pop(-1)
                    shortest.pop(-1)
                else:
                    longuest.pop(-1)
            except IndexError:
                shortest.pop()

    return x + list(reversed(y))


class Node:
    """Class representing a child in a tree
    """

    _case = True
    """If True, the search trought the tree is case sensitive"""

    def __init__(self, name, subtree=None):

        if not isinstance(subtree, (list, type(None))):
            raise TypeError("subtree should be list or None, %s given" % type(subtree))

        self.name = name
        self.subtree = subtree

    def __repr__(self):  # pragma: no cover
        return "<{} '{}'>".format(self.__class__.__name__, self.name)

    def __getitem__(self, item):
        return self.walk(item)[0]

    def __contains__(self, item):
        """Special method for membership test (e.g. ``if 'B' in node``).
        """
        if self.name == item or (not self._case and self.name.lower() == item.lower()):
            return True
        try:
            self._walk(item)
        except ValueError:
            return False
        else:
            return True

    def _walk(self, goal, subtree=None):
        """
        Args:
            goal (str)
            subtree (list optional)
        Returns:
            list
        """

        if subtree is None:
            subtree = self.subtree

        for node in subtree:
            if node.name == goal or (not self._case and node.name.lower() == goal.lower()):
                return [node]
            elif node.subtree:
                try:
                    res = self._walk(goal, node.subtree)
                except ValueError:
                    # print("Not in %s" % node.name)
                    continue
                else:
                    break
        else:
            raise ValueError("'{}' not found".format(goal))

        return res + [node]

    def walk(self, goal):
        """Get the shortest path between ``self`` and ``goal``

        Args:
            goal (str): Name of the node you want to reach
        Return:
            list: List of nodes
        """
        # This method is only here to insert the top node in the loop
        name = self.name
        if not self._case:
            goal = goal.lower()
            name = self.name.lower()

        return self._walk(goal) + [self] if goal != name else [self]

    def path(self, start, stop):
        """Get the sortest path to go from one node to an other

        Args:
            start (str): Name of the source node
            stop (str): Name of node you want to reach
        Returns:
            list: List of nodes names
        """

        start = start.name if isinstance(start, self.__class__) else start
        stop = stop.name if isinstance(stop, self.__class__) else stop

        x = self.walk(start)
        y = self.walk(stop)

        final = _merge(x, y)

        return final

    def steps(self, start, stop):
        """Same as :py:meth:`path` but gives a list of couple

        Args:
            start (str): Name of the source node
            stop (str): Name of node you want to reach
        Returns:
            list: List of nodes names
        """
        path = self.path(start, stop)
        for i in range(len(path) - 1):
            yield path[i], path[i + 1]


class Route:
    """Class used by :py:class:`Node2` to describe where to find
    another node.
    """

    def __init__(self, direction, steps):
        self.direction = direction
        self.steps = steps

    def __repr__(self):  # pragma: no cover
        return "<d={0}, s={1}>".format(self.direction, self.steps)


class Node2:
    """Class representing a node in a graph, relations may be circular.

    .. code-block:: python

        A = Node2('A')
        B = Node2('B')
        C = Node2('C')
        D = Node2('D')
        E = Node2('E')
        F = Node2('F')

        A + B + C + D + E + F + A
        F + C

        #   A
        #  / \\
        # B   F
        # | / |
        # C   E
        #  \ /
        #   D

        A.path('E')
        # [A, F, E]
        A.steps('E')
        # [(A, F), (F, E)]
        E.path('B')
        # [E, F, A, B] or [E, D, C, B]
    """

    def __init__(self, name):
        """
        Args:
            name (str): Name of the node. Will be used for graph searching
        """
        self.name = name
        """Name of the node
        """

        self.neighbors = OrderedDict()
        """List of all direct neighbors in the graph.
        OrderedDict is only used as OrderedSet, so only the keys of the dict matter
        """

        self.routes = {}
        """Route mapping. Where direction to follow in order to reach a
        particular target
        """

    def __add__(self, other):
        self.neighbors[other] = None
        other.neighbors[self] = None
        self._update()
        return other

    def _update(self, already_updated=None):

        self.routes = {}
        for node in self.neighbors:
            self.routes[node.name] = Route(node, 1)

            # Retrieve route from neighbors
            for name, route in node.routes.items():

                # check if the node actually at hand (name) is not already
                # a direct neighbor of self
                if name in [self.name] + [x.name for x in self.neighbors]:
                    continue

                # check if the node actually at hand (name) is not already
                # integrated in the self.routes or if it already is, if the
                # path is shorter
                if name in self.routes.keys() and self.routes[name].steps <= route.steps:
                    continue

                self.routes[name] = Route(node, route.steps + 1)

        # This set serves as a shared lock, every object that is in this set
        # won't be updated by others. This is to avoid infinite recursions
        if already_updated is None:
            already_updated = set()

        already_updated.add(self)

        # Recursive update (with lock)
        for node in self.neighbors:
            if node not in already_updated:
                node._update(already_updated)

    def path(self, goal):
        """Get the shortest way between two nodes of the graph

        Args:
            goal (str): Name of the targeted node
        Return:
            list of Node2
        """
        if goal == self.name:
            return [self]

        if goal not in self.routes:
            raise ValueError("Unknown '{0}'".format(goal))

        obj = self
        path = [obj]
        while True:
            obj = obj.routes[goal].direction
            path.append(obj)
            if obj.name is goal:
                break
        return path

    def steps(self, goal):
        """Get the list of individual relations leading to the targeted node

        Args:
            goal (str): Name of the targeted node
        Return:
            list of tuple of Node2
        """

        path = self.path(goal)
        for i in range(len(path) - 1):
            yield path[i], path[i + 1]

    def __str__(self):  # pragma: no cover
        return self.name

    def __repr__(self):  # pragma: no cover
        return "<{} '{}'>".format(self.__class__.__name__, self.name)
