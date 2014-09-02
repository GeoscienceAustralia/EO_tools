#!/usr/bin/env python

# ===============================================================================
# Copyright (c)  2014 Geoscience Australia
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither Geoscience Australia nor the names of its contributors may be
#       used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ===============================================================================

'''Unit test for vincenty.py'''

from __future__ import absolute_import
from __future__ import print_function
import unittest
import math
from bodies.vincenty import vinc_dist, vinc_pt, GreatCircle


class VincentyTestCase(unittest.TestCase):

    def runTest(self):
        # WGS84
        a = 6378137.0
        b = 6356752.3142
        f = (a - b) / a

        print("\n Ellipsoidal major axis =  %12.3f metres\n" % (a))
        print("\n Inverse flattening     =  %15.9f\n" % (1.0 / f))

        print("\n Test Flinders Peak to Buninyon")
        print("\n ****************************** \n")
        phi1 = -((3.7203 / 60. + 57) / 60. + 37)
        lembda1 = (29.5244 / 60. + 25) / 60. + 144
        print("\n Flinders Peak = %12.6f, %13.6f \n" % (phi1, lembda1))
        deg = int(phi1)
        minn = int(abs((phi1 - deg) * 60.0))
        sec = abs(phi1 * 3600 - deg * 3600) - minn * 60
        print(" Flinders Peak =   %3i\xF8%3i\' %6.3f\",  " % (deg, minn, sec), end=' ')
        deg = int(lembda1)
        minn = int(abs((lembda1 - deg) * 60.0))
        sec = abs(lembda1 * 3600 - deg * 3600) - minn * 60
        print(" %3i\xF8%3i\' %6.3f\" \n" % (deg, minn, sec))

        phi2 = -((10.1561 / 60. + 39) / 60. + 37)
        lembda2 = (35.3839 / 60. + 55) / 60. + 143
        print("\n Buninyon      = %12.6f, %13.6f \n" % (phi2, lembda2))

        deg = int(phi2)
        minn = int(abs((phi2 - deg) * 60.0))
        sec = abs(phi2 * 3600 - deg * 3600) - minn * 60
        print(" Buninyon      =   %3i\xF8%3i\' %6.3f\",  " % (deg, minn, sec), end=' ')
        deg = int(lembda2)
        minn = int(abs((lembda2 - deg) * 60.0))
        sec = abs(lembda2 * 3600 - deg * 3600) - minn * 60
        print(" %3i\xF8%3i\' %6.3f\" \n" % (deg, minn, sec))

        dist, alpha12, alpha21 = vinc_dist(
            f, a, math.radians(phi1), math.radians(lembda1), math.radians(phi2), math.radians(lembda2))

        alpha12 = math.degrees(alpha12)
        alpha21 = math.degrees(alpha21)

        print("\n Ellipsoidal Distance = %15.3f metres\n            should be         54972.271 m\n" % (dist))
        print("\n Forward and back azimuths = %15.6f, %15.6f \n" % (alpha12, alpha21))
        deg = int(alpha12)
        minn = int(abs((alpha12 - deg) * 60.0))
        sec = abs(alpha12 * 3600 - deg * 3600) - minn * 60
        print(" Forward azimuth = %3i\xF8%3i\' %6.3f\"\n" % (deg, minn, sec))
        deg = int(alpha21)
        minn = int(abs((alpha21 - deg) * 60.0))
        sec = abs(alpha21 * 3600 - deg * 3600) - minn * 60
        print(" Reverse azimuth = %3i\xF8%3i\' %6.3f\"\n" % (deg, minn, sec))

        # Test the direct function */
        phi1 = -((3.7203 / 60. + 57) / 60. + 37)
        lembda1 = (29.5244 / 60. + 25) / 60. + 144
        dist = 54972.271
        alpha12 = (5.37 / 60. + 52) / 60. + 306
        phi2 = lembda2 = 0.0
        alpha21 = 0.0

        phi2, lembda2, alpha21 = vinc_pt(f, a, math.radians(phi1), math.radians(lembda1), math.radians(alpha12), dist)

        phi2 = math.degrees(phi2)
        lembda2 = math.degrees(lembda2)
        alpha21 = math.degrees(alpha21)

        print("\n Projected point =%11.6f, %13.6f \n" % (phi2, lembda2))
        deg = int(phi2)
        minn = int(abs((phi2 - deg) * 60.0))
        sec = abs(phi2 * 3600 - deg * 3600) - minn * 60
        print(" Projected Point = %3i\xF8%3i\' %6.3f\", " % (deg, minn, sec), end=' ')
        deg = int(lembda2)
        minn = int(abs((lembda2 - deg) * 60.0))
        sec = abs(lembda2 * 3600 - deg * 3600) - minn * 60
        print("  %3i\xF8%3i\' %6.3f\"\n" % (deg, minn, sec))
        print(" Should be Buninyon \n")
        print("\n Reverse azimuth = %10.6f \n" % (alpha21))
        deg = int(alpha21)
        minn = int(abs((alpha21 - deg) * 60.0))
        sec = abs(alpha21 * 3600 - deg * 3600) - minn * 60
        print(" Reverse azimuth = %3i\xF8%3i\' %6.3f\"\n\n" % (deg, minn, sec))

        # lat/lon of New York
        lat1 = 40.78
        lon1 = -73.98
        # lat/lon of London.
        lat2 = 51.53
        lon2 = 0.08
        print('New York to London:')
        gc = GreatCircle((2 * a + b) / 3., (2 * a + b) / 3., lon1, lat1, lon2, lat2)
        print('geodesic distance using a sphere with WGS84 mean radius = ', gc.distance)
        print('lon/lat for 10 equally spaced points along geodesic:')
        lons, lats = gc.points(10)
        for lon, lat in zip(lons, lats):
            print(lon, lat)
        gc = GreatCircle(a, b, lon1, lat1, lon2, lat2)
        print('geodesic distance using WGS84 ellipsoid = ', gc.distance)
        print('lon/lat for 10 equally spaced points along geodesic:')
        lons, lats = gc.points(10)
        for lon, lat in zip(lons, lats):
            print(lon, lat)


def the_suite():
    """Returns a test suite of all the tests in this module."""

    test_classes = [
        VincentyTestCase
    ]

    suite_list = map(unittest.defaultTestLoader.loadTestsFromTestCase,
                     test_classes)

    suite = unittest.TestSuite(suite_list)

    return suite

#
# Run unit tests if in __main__
#

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(the_suite())
