from pytest import raises

from space.utils.tree import Tree, Node

M = Node("M", None)
L = Node("L", None)
K = Node("K", [L, M])
J = Node("J", None)
I = Node("I", None)
H = Node("H", [J])
G = Node("G", None)
F = Node("F", [H, I])
E = Node("E", [F, G])
D = Node("D", None)
C = Node("C", None)
B = Node("B", [C, D])
A = Node("A", [B, E, K])

# Equivalent to

# A = Node("A", [
#     Node("B", [
#         Node("C", None),
#         Node("D", None)
#     ]),
#     Node("E", [
#         Node("F", [
#             Node("H", [
#                 Node("J", None)
#             ]),
#             Node("I", None)
#         ]),
#         Node("G", None)
#     ]),
#     Node("K", [
#         Node("L", None),
#         Node("M", None)
#     ])
# ])


def test_path():

    tree = Tree(A)

    assert tree.path('B', 'E') == ['B', 'A', 'E']
    assert tree.path('H', 'E') == ['H', 'F', 'E']
    assert tree.path('H', 'G') == ['H', 'F', 'E', 'G']
    assert tree.path('H', 'A') == ['H', 'F', 'E', 'A']
    assert tree.path('B', 'A') == ['B', 'A']
    assert tree.path('J', 'I') == ['J', 'H', 'F', 'I']
    assert tree.path('C', 'B') == ['C', 'B']
    assert tree.path('J', 'M') == ['J', 'H', 'F', 'E', 'A', 'K', 'M']
    assert tree.path('M', 'J') == ['M', 'K', 'A', 'E', 'F', 'H', 'J']
    assert tree.path('F', 'A') == ['F', 'E', 'A']
    assert tree.path('A', 'F') == ['A', 'E', 'F']

    assert tree.path("L", "L") == ['L']


def test_wrong_arg():

    with raises(TypeError):
        Tree([A])

    with raises(TypeError):
        Node("X", (Node("Y", (Node("Z")))))


def test_contain():

    tree = Tree(A)

    assert ("Z" in tree) is False
    assert ("G" in tree) is True
