#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises

from beyond.utils.node import Node

A = Node('A')
B = Node('B')
C = Node('C')
D = Node('D')
E = Node('E')
F = Node('F')
G = Node('G')
H = Node('H')
I = Node('I')
J = Node('J')
K = Node('K')
L = Node('L')
M = Node('M')

A + B + C + D + A
D + E + F
E + A
C + G + H + I + B
D + J + K + H
E + L + M

#  F---E---L---M
#     / \
#    D---A
#  / |   |
# J  C---B
# |  |   |
# K  G   I
# |   \ /
# `----H


def test_path():

    assert A.path('A') == [A]
    assert A.path('B') == [A, B]
    assert A.path('C') == [A, D, C]
    assert A.path('D') == [A, D]
    assert A.path('E') == [A, E]
    assert A.path('F') == [A, E, F]
    assert A.path('G') == [A, D, C, G]
    assert A.path('H') == [A, B, I, H]
    assert A.path('I') == [A, B, I]
    assert A.path('J') == [A, D, J]
    assert A.path('K') == [A, D, J, K]
    assert A.path('L') == [A, E, L]
    assert A.path('M') == [A, E, L, M]

    with raises(ValueError):
        A.path('Z')


def test_steps():
    assert list(A.steps('B')) == [(A, B)]
    assert list(A.steps('C')) == [(A, D), (D, C)]
    assert list(A.steps('D')) == [(A, D)]
    assert list(A.steps('E')) == [(A, E)]
    assert list(A.steps('F')) == [(A, E), (E, F)]
    assert list(A.steps('G')) == [(A, D), (D, C), (C, G)]
    assert list(A.steps('H')) == [(A, B), (B, I), (I, H)]
    assert list(A.steps('I')) == [(A, B), (B, I)]
    assert list(A.steps('J')) == [(A, D), (D, J)]
    assert list(A.steps('K')) == [(A, D), (D, J), (J, K)]
    assert list(A.steps('L')) == [(A, E), (E, L)]
    assert list(A.steps('M')) == [(A, E), (E, L), (L, M)]


def test_list():

    assert A in A.list
    assert B in A.list
    assert C in A.list
    assert D in A.list
    assert E in A.list
    assert F in A.list
    assert G in A.list
    assert H in A.list
    assert I in A.list
    assert J in A.list
    assert K in A.list
    assert L in A.list
    assert M in A.list
