from pytest import raises

from beyond.io.ccsds import dumps, loads, CcsdsParseError


def test_dummy(ccsds_format):

    with raises(TypeError):
        dumps(None, fmt=ccsds_format)

    with raises(CcsdsParseError):
        loads("dummy text")
