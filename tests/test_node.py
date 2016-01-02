from pytest import raises

from space.utils.node import Node

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


def test_repr():
    assert repr(A) == "<Node 'A'>"


def test_path():

    assert A.path('B', 'E') == [B, A, E]
    assert A.path('H', 'E') == [H, F, E]
    assert A.path('H', 'G') == [H, F, E, G]
    assert A.path('H', 'A') == [H, F, E, A]
    assert A.path('B', 'A') == [B, A]
    assert A.path('J', 'I') == [J, H, F, I]
    assert A.path('C', 'B') == [C, B]
    assert A.path('J', 'M') == [J, H, F, E, A, K, M]
    assert A.path('M', 'J') == [M, K, A, E, F, H, J]
    assert A.path('F', 'A') == [F, E, A]
    assert A.path('A', 'F') == [A, E, F]

    assert A.path("L", "L") == [L]


def test_wrong_arg():

    with raises(TypeError):
        A([A])

    with raises(TypeError):
        Node("X", (Node("Y", (Node("Z")))))


def test_contain():

    assert ("Z" in A) is False
    assert ("G" in A) is True
    assert ("A" in A) is True
