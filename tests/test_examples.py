"""There is some examples of utilisation of beyond in the doc and the README
these tests are here to check if they still are valid, as the library evolves
"""

from pytest import fixture, mark
from pathlib import Path
from subprocess import run


@fixture(params=['docking', 'ground-track', 'hohmann', 'listeners', 'station', "cw_vs_ya"])
def cases(request):

    folder = Path(__file__).parent.parent / "doc" / "source" / "_static"
    return folder / (request.param + ".py")


@mark.mpl
def test_doc(cases):

    p = run(["python", cases, "no-display"])
    assert p.returncode == 0


def test_readme():

    filepath = Path(__file__).parent.parent / "README.rst"

    start = 0
    code = []
    for i, line in enumerate(filepath.open().read().splitlines()):
        if not line:
            continue
        elif line.startswith('.. code-block:: python'):
            start = i + 2
            continue
        elif start and line.startswith('    '):
            code.append(line[4:])
        elif start:
            break

    code = "\n".join(code)

    exec(code)
