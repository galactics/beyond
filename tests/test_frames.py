#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest.mock import patch
from space.utils.dates import Date
from space.frames.nutation import sideral

def test_nutation_1980():
    with patch('space.frames.poleandtimes.TimeScales.get') as mock_ts:
        mock_ts.return_value = (-32.4399519, -0.4399619, 32)

        with patch('space.frames.poleandtimes.PolePosition.get') as mock_pole:
            mock_pole.return_value = {
                'X': -0.140682,
                'Y': 0.333309,
                'dpsi': 52.195,
                'deps': -3.875
            }
            date = Date(2004, 4, 6, 7, 51, 28, 386009)

            # Check that the conversion is well done
            assert str(date.change_scale('UT1')) == "2004-04-06T07:51:27.946047 UT1"

            gmst = sideral(date)
            assert gmst == 312.80989426211454

            # lst = sideral(date, longitude=-104)
            # print(lst)
            gast = sideral(date, model='apparent')
            print(gast)

    assert gast == 312.8063654
    # gast = sideral(date, model='apparent')
    # print(gast)