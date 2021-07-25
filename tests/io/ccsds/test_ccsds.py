import xmlschema
from pathlib import Path
from pytest import raises

from beyond.io.ccsds import dumps, loads, CcsdsError


def test_dummy(ccsds_format):

    with raises(TypeError):
        dumps(None, fmt=ccsds_format)

    with raises(CcsdsError):
        loads("dummy text")


def test_xsd(helper):

    folder = Path(__file__).parent.joinpath("data/")
    xsdpath = folder.joinpath("xsd/ndmxml-1.0-master.xsd")

    schema = xmlschema.XMLSchema(str(xsdpath))

    failing = {"opm_strange_units.xml": "attribute units='m': value must be one of ['km']"}

    for file in folder.glob("*.xml"):
        if file.name not in failing:
            assert schema.is_valid(str(file))
        else:
            assert not schema.is_valid(str(file))
            with raises(xmlschema.validators.exceptions.XMLSchemaValidationError) as e:
                schema.validate(str(file))

            assert e.value.reason == failing[file.name]

