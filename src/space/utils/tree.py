#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module helps to find the shortest path between two element of a
hierarchy
"""

# TODO
#   Possibly merge Node and Tree into a sole class that could walk itself


class Node:
    """Class representing a child in the tree
    """

    def __init__(self, name, subtree=None):

        if type(subtree) not in (list, type(None)):
            raise TypeError("subtree should be list or None, %s given" % type(subtree))

        self.name = name
        self.subtree = subtree


class Tree:
    """Class representing the tree to search for nodes
    """

    def __init__(self, top_node):

        if not isinstance(top_node, Node):
            raise TypeError("top_node should be a Node object")

        self.tree = [top_node]

    def __contains__(self, item):
        """Special method for membership test (e.g. ``if 'B' in tree``).
        """
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
            subtree = self.tree

        for node in subtree:
            if node.name == goal:
                return [node.name]
            elif node.subtree:
                try:
                    res = self._walk(goal, node.subtree)
                except:
                    # print("Not in %s" % node.name)
                    continue
                else:
                    return res + [node.name]
        else:
            raise ValueError(goal + " introuvable")

    def _merge(self, x, y):
        """Remove commons ancestors and concatenate two passes

        Args:
            x (list)
            y (list)
        Returns:
            list
        """

        shortest, longuest = sorted((x, y), key=len)
        for i in range(-len(shortest), 0):
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

    def path(self, start, stop):
        """Get the sortest path to go from one node to an other

        Args:
            start (str): Name of the source node
            stop (str): Name of node you want to reach
        Returns:
            list: List of nodes names
        """

        start = start.name if type(start) is Node else start
        stop = stop.name if type(stop) is Node else stop

        x = self._walk(start)
        y = self._walk(stop)

        final = self._merge(x, y)

        return final
