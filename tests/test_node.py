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


def test_steps():

    assert list(A.steps('B', 'E')) == [(B, A), (A, E)]
    assert list(A.steps('H', 'E')) == [(H, F), (F, E)]
    assert list(A.steps('H', 'G')) == [(H, F), (F, E), (E, G)]
    assert list(A.steps('H', 'A')) == [(H, F), (F, E), (E, A)]
    assert list(A.steps('B', 'A')) == [(B, A)]
    assert list(A.steps('J', 'I')) == [(J, H), (H, F), (F, I)]
    assert list(A.steps('C', 'B')) == [(C, B)]
    assert list(A.steps('J', 'M')) == [(J, H), (H, F), (F, E), (E, A), (A, K), (K, M)]
    assert list(A.steps('M', 'J')) == [(M, K), (K, A), (A, E), (E, F), (F, H), (H, J)]
    assert list(A.steps('F', 'A')) == [(F, E), (E, A)]
    assert list(A.steps('A', 'F')) == [(A, E), (E, F)]
    assert list(A.steps("L", "L")) == []


def test_wrong_arg():

    with raises(TypeError):
        A([A])

    with raises(TypeError):
        Node("X", (Node("Y", (Node("Z")))))


def test_contain():

    assert ("Z" in A) is False
    assert ("G" in A) is True
    assert ("A" in A) is True


def test_getitem():

    assert A["G"] is G
    assert A["A"] is A


def test_case():

    class Node2(Node):
        _case = False

    M = Node2("M", None)
    L = Node2("L", None)
    K = Node2("K", [L, M])
    J = Node2("J", None)
    I = Node2("I", None)
    H = Node2("H", [J])
    G = Node2("G", None)
    F = Node2("F", [H, I])
    E = Node2("E", [F, G])
    D = Node2("D", None)
    C = Node2("C", None)
    B = Node2("B", [C, D])
    A = Node2("A", [B, E, K])

    assert ("z" in A) is False
    assert ("g" in A) is True
    assert ("a" in A) is True

    assert A["g"] is G
    assert A["a"] is A

    assert A.path('j', 'm') == [J, H, F, E, A, K, M]
