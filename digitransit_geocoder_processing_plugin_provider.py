# digitransit_geocoder_processing_plugin_provider.py
#
# Created
#  by Erno Mäkinen (erno@gispo.fi)
#  on 24.3.2018

from qgis.core import QgsProcessingProvider
from .digitransit_geocoder_processing_plugin_algorithm import DigitransitGeocoderPluginAlgorithm


class DigitransitProcessingPluginProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """

        # Load algorithms
        alglist = [DigitransitGeocoderPluginAlgorithm()]

        for alg in alglist:
            self.addAlgorithm( alg )

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'digitransitgeocoder'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('Digitransit.fi geocoding plugin')

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
