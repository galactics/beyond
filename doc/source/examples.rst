Examples of utilisation
=======================

Ground track
------------

.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import timedelta

    from space.orbits import Tle
    from space.utils import Date


    # Parsing of TLE
    tle = Tle("""ISS (ZARYA)             
    1 25544U 98067A   16086.49419020  .00003976  00000-0  66962-4 0  9998
    2 25544  51.6423 110.4590 0001967   0.7896 153.8407 15.54256299992114""")

    # Conversion into `Orbit` object
    orb = tle.orbit()

    # Tables containing the positions of the ground track
    latitudes, longitudes = [], []
    for point in orb.ephemeris(Date.now(), timedelta(minutes=120), timedelta(minutes=1)):

        # Conversion to earth rotating frame
        point.change_frame('ITRF')

        # Conversion from cartesian to spherical coordinates (range, latitude, longitude)
        point.change_form('spherical')

        # Conversion from radians to degrees
        lat, lon = np.degrees(point[1:3])

        latitudes.append(lat)
        longitudes.append(lon)

    im = plt.imread("earth.png")
    plt.figure(figsize=(15.2, 8.2))
    plt.imshow(im, extent=[-180, 180, -90, 90])
    plt.plot(longitudes, latitudes, 'r.')

    plt.xlim([-180, 180])
    plt.ylim([-90, 90])
    plt.grid(True, color='w')
    plt.xticks(range(-180, 181, 30))
    plt.yticks(range(-90, 91, 30))
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    plt.show()

.. image:: _static/ground-track-ISS.png

Station pointings
-----------------

.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import timedelta

    from space.utils import Date
    from space.orbits import Tle
    from space.frames import create_station

    tle = Tle("""ISS (ZARYA)             
    1 25544U 98067A   16086.49419020  .00003976  00000-0  66962-4 0  9998
    2 25544  51.6423 110.4590 0001967   0.7896 153.8407 15.54256299992114""").orbit()

    # Station definition
    station = create_station('Aus', (43.428889, 1.497778, 178.0))
    azims, elevs = [], []

    print("    Time      Azim    Elev    Distance   Radial Velocity")
    print("===============================================================")

    for orb in station.visibility(tle, start=Date.now(), stop=timedelta(hours=24), step=timedelta(seconds=30), events=True):
        azim = np.degrees(np.pi - orb[2])
        elev = np.degrees(orb[1])

        # Archive for plotting
        azims.append(azim)
        elevs.append(90 - elev)   # Matplotlib actually force 0 to be at the center, so we trick it by inverting the values

        r = orb.r / 1000.  
        print("{orb.info:3} {orb.date:%H:%M:%S} {azim:7.2f} {elev:7.2f} {r:10.2f} {orb.r_dot:10.2f}".format(
            orb=orb, r=r, azim=azim, elev=elev
        ))

        if orb.info == "LOS":
            # We stop at the end of the first pass
            print()
            break

    plt.figure()
    ax = plt.subplot(111, projection='polar')
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('N')
    plt.plot(np.radians(azims), elevs, '.')
    ax.set_yticks(range(0, 90, 20))
    ax.set_yticklabels(map(str, range(90, 0, -20)))
    ax.set_rmax(90)

    plt.show()

which gives

.. code-block:: text

        Time      Azim    Elev    Distance   Radial Velocity
    ===============================================================
    AOS 02:01:23  302.10   -0.00    2312.91   -6906.48
        02:01:39  302.30    1.00    2204.46   -6904.71
        02:02:09  302.71    3.07    1997.46   -6894.10
        02:02:39  303.20    5.39    1790.94   -6870.86
        02:03:09  303.79    8.08    1585.39   -6829.11
        02:03:39  304.54   11.30    1381.49   -6758.37
        02:04:09  305.53   15.29    1180.37   -6638.85
        02:04:39  306.94   20.51     984.03   -6430.17
        02:05:09  309.17   27.78     796.31   -6042.60
        02:05:39  313.28   38.63     625.31   -5262.66
        02:06:09  323.59   55.36     489.17   -3610.39
        02:06:39   12.81   74.28     423.23    -565.54
    MAX 02:06:43   30.39   75.00     421.90       0.00
        02:07:09   90.23   61.99     458.89    2806.46
        02:07:39  105.74   43.24     577.62    4871.54
        02:08:09  111.00   30.79     740.40    5857.82
        02:08:39  113.63   22.61     924.12    6336.73
        02:09:09  115.23   16.86    1118.38    6588.72
        02:09:39  116.32   12.54    1318.37    6730.93
        02:10:09  117.12    9.12    1521.66    6814.75
        02:10:39  117.74    6.29    1726.92    6864.71
        02:11:09  118.24    3.86    1933.33    6893.49
        02:11:39  118.65    1.72    2140.39    6908.11
    LOS 02:12:05  118.97    0.01    2323.42    6912.59

.. image:: _static/station.png