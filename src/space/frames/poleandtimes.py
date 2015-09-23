
from pathlib import Path
import datetime
# from collections import OrderedDict

__all__ = ['PolePosition', 'TimeScales']


class TimeScales:

    @classmethod
    def get(cls, date):
        ut1_utc = Finals2000A().data[date]['time']['UT1-UTC']
        tai_utc = TaiUtc.get(date)
        # print("UT1-UTC", ut1_utc)
        # print("TAI-UTC", tai_utc)
        ut1_tai = ut1_utc - tai_utc
        return ut1_tai, ut1_utc, tai_utc


class PolePosition:
    pass


class TaiUtc():

    path = Path(__file__).parent / "data" / "tai-utc.txt"
    _data = []

    @classmethod
    def _initialise(cls):
        if not cls._data:

            _date = lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date()
            with cls.path.open() as f:
                lines = f.read().splitlines()

            for line in lines:
                if line.startswith("#"):
                    continue

                start, stop, value = line.split()
                start, stop = _date(start), _date(stop)
                value = int(value)
                cls._data.append(
                    (start, stop, value)
                )

    @classmethod
    def get(cls, date):
        cls._initialise()
        tmp = cls()._data[0][2]
        for start, stop, value in cls()._data:
            if start <= date < stop:
                tmp = value
        return tmp


class Finals2000A():

    path = Path(__file__).parent / "data" / "finals2000A.data"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):

        # self.data = OrderedDict()
        self.data = {}

        with self.path.open() as f:
            lines = f.read().splitlines()

        for line in lines:
            line = line.strip()
            mjd = int(float(line[7:15]))
            date = datetime.date.fromordinal(678576 + mjd)

            try:
                self.data[date] = {
                    'mjd': mjd,
                    'pole': {
                        'flag': line[16],
                        'X': float(line[18:27]),
                        # 'Xerror': float(line[27:36]),
                        'Y': float(line[37:46]),
                        # 'Yerror': float(line[46:55])
                    },
                    'time': {
                        'UT1-UTC': float(line[58:68])
                    }
                }
            except IndexError:
                break


if __name__ == '__main__':

    dates = [
        datetime.date(1992, 1, 1),
        datetime.date(1999, 1, 1),
        datetime.date(2014, 8, 12),
        datetime.date(2015, 2, 27),
        datetime.date.today(),
    ]

    for date in dates:
        print(date, TimeScales.get(date))
