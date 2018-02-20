# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DigitransitGeocoder
                                 A QGIS plugin
 The plugin is meant for geocoding Finnish addresses
                             -------------------
        begin                : 2018-02-20
        copyright            : (C) 2018 by Gispo, Ltd.
        email                : erno@gispo.fi
        git sha              : $Format:%H$
 ***************************************************************************/

 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load DigitransitGeocoder class from file DigitransitGeocoder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .digitransit_geocoder import DigitransitGeocoder
    return DigitransitGeocoder(iface)
