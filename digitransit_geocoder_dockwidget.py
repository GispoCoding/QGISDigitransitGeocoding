# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DigitransitGeocoderDialog
                                 A QGIS plugin
 The plugin is meant for geocoding Finnish addresses
                             -------------------
        begin                : 2018-02-20
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Gispo, Ltd.
        email                : erno@gispo.fi
 ***************************************************************************/

"""

import os

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, QMetaObject, pyqtSlot, QVariant, QCoreApplication
from PyQt5.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsMessageLog
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl
import json
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsProject,\
    QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt5.QtCore import QSettings

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'digitransit_geocoder_dockwidget_base.ui'))


class DigitransitGeocoderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    DEFAULT_MAX_NUMBER_OF_RESULTS = 10
    DEFAULT_SEARCH_MAP_CANVAS_AREA = False
    DEFAULT_USE_NLS_DATA = True
    DEFAULT_USE_OA_DATA = True
    DEFAULT_USE_OSM_DATA = True
    DEFAULT_SEARCH_ADDRESS = True
    DEFAULT_SEARCH_VENUE = True
    DEFAULT_SEARCH_STREET = True
    DEFAULT_MINIMUM_CONFIDENCE_VALUE = 0.5
    DEFAULT_SHOW_ALL_RESULTS_ON_MAP = True


    closingPlugin = pyqtSignal()

    def __init__(self, iface,
                 parent=None):
        """Constructor."""
        super(DigitransitGeocoderDockWidget, self).__init__(parent)

        self.iface = iface

        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Note: no need to call the QMetaObject.connectSlotsByName(self)
        #QMetaObject.connectSlotsByName(self)

        # Note this is not because we have the auto connection
        #self.pushButtonSearch.clicked.connect(self.handleSearch)

        self.network_access_manager = QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handleSearchResponse)

        self.listWidgetGeocodingResults.itemClicked.connect(self.handleSearchResultSelected)

        self.spinBoxMaxResults.setValue(
            QSettings().value("/DigitransitGeocoder/maxNumberOfResults",
                              DigitransitGeocoderDockWidget.DEFAULT_MAX_NUMBER_OF_RESULTS,
                              type=int))
        self.checkBoxSearchMapCanvasArea.setChecked(
            QSettings().value("/DigitransitGeocoder/searchMapCanvasArea",
                              DigitransitGeocoderDockWidget.DEFAULT_SEARCH_MAP_CANVAS_AREA,
                              type=bool))
        self.checkBoxNLS.setChecked(
            QSettings().value("/DigitransitGeocoder/useNLSData",
                              DigitransitGeocoderDockWidget.DEFAULT_USE_NLS_DATA,
                              type=bool))
        self.checkBoxOA.setChecked(
            QSettings().value("/DigitransitGeocoder/useOAData",
                              DigitransitGeocoderDockWidget.DEFAULT_USE_OA_DATA,
                              type=bool))
        self.checkBoxOSM.setChecked(
            QSettings().value("/DigitransitGeocoder/useOSMData",
                              DigitransitGeocoderDockWidget.DEFAULT_USE_OSM_DATA,
                              type=bool))
        self.checkBoxSearchAddress.setChecked(
            QSettings().value("/DigitransitGeocoder/searchAddress",
                              DigitransitGeocoderDockWidget.DEFAULT_SEARCH_ADDRESS,
                              type=bool))
        self.checkBoxSearchVenue.setChecked(
            QSettings().value("/DigitransitGeocoder/searchVenue",
                              DigitransitGeocoderDockWidget.DEFAULT_SEARCH_VENUE,
                              type=bool))
        self.checkBoxSearchStreet.setChecked(
            QSettings().value("/DigitransitGeocoder/searchStreet",
                              DigitransitGeocoderDockWidget.DEFAULT_SEARCH_STREET,
                              type=bool))
        self.horizontalSliderMinimumConfidenceValue.setValue(
            QSettings().value("/DigitransitGeocoder/minConfidenceValue",
                              DigitransitGeocoderDockWidget.DEFAULT_MINIMUM_CONFIDENCE_VALUE * 100,
                              type=float))
        self.radioButtonResultsShowAll.setChecked(
            QSettings().value("/DigitransitGeocoder/showAllResultsOnMap",
                              DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP,
                              type=bool))
        self.radioButtonResultsShowSelected.setChecked(
            QSettings().value("/DigitransitGeocoder/showSelectedResultOnMap",
                              not DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP,
                              type=bool))

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    #def handleSearch(self):
    #    QgsMessageLog.logMessage('This is an important message',
    #                             'Important Information',
    #                             Qgis.Info)

    @pyqtSlot() # Without this the signal is handled twice, see https://stackoverflow.com/questions/14311578/event-signal-is-emmitted-twice-every-time
    def on_pushButtonSearch_clicked(self):
        #QMessageBox.information(None,
        #                        'Important Information',
        #                        'This is an important message')

        #QgsMessageLog.logMessage(self.lineEditAddress.text(), 'DigitransitGeocoder', Qgis.Info)

        self.search_text = self.lineEditAddress.text()
        if len(self.search_text) == 0:
            return
        self.geocode(self.search_text)

    def geocode(self, search_text):
        base_URL = "http://api.digitransit.fi/geocoding/v1/search"
        size = self.spinBoxMaxResults.value()
        search_URL = base_URL + "?text=" + search_text + '&size=' +str(size)

        if self.checkBoxNLS.isChecked() or self.checkBoxOA.isChecked() or self.checkBoxOSM.isChecked():
            sources = "&sources="
            if self.checkBoxNLS.isChecked():
                sources = sources + "nlsfi,"
            if self.checkBoxOA.isChecked():
                sources = sources + "oa,"
            if self.checkBoxOSM.isChecked():
                sources = sources + "osm,"
            search_URL = search_URL + sources.rstrip(',')
        else:
            QMessageBox.information(self.iface.mainWindow(),
                                    self.tr(u'No data sources selected'),
                                    self.tr(u'Please, select at least one data source'))
            return

        if self.checkBoxSearchAddress.isChecked() or self.checkBoxSearchVenue.isChecked() or self.checkBoxSearchStreet.isChecked():
            layers = "&layers="
            if self.checkBoxSearchAddress.isChecked():
                layers = layers + "address,"
            if self.checkBoxSearchVenue.isChecked():
                layers = layers + "venue,"
            if self.checkBoxSearchStreet.isChecked():
                layers = layers + "street,"
            search_URL = search_URL + layers.rstrip(',')
        else:
            QMessageBox.information(self.iface.mainWindow(),
                                    self.tr(u'No types of locations selected'),
                                    self.tr(u'Please, select at least one type of location to search'))
            return

        if self.checkBoxSearchMapCanvasArea.isChecked():
            extent = self.iface.mapCanvas().extent() # QgsRectangle
            min_lon = extent.xMinimum()
            min_lat = extent.yMinimum()
            max_lon = extent.xMaximum()
            max_lat = extent.yMaximum()

            source_crs = QgsProject.instance().crs()
            dest_crs = QgsCoordinateReferenceSystem(4326)
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            dest_min_point = transform.transform(QgsPointXY(min_lon, min_lat))
            dest_max_point = transform.transform(QgsPointXY(max_lon, max_lat))

            #"boundary.rect.min_lon"
            # QgsMessageLog.logMessage(str(source_crs.authid()), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(min_lon), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(min_lat), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(max_lon), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(max_lat), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(dest_min_point.x()), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(dest_min_point.y()), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(dest_max_point.x()), "DigitransitGeocoder", Qgis.Info)
            # QgsMessageLog.logMessage(str(dest_max_point.y()), "DigitransitGeocoder", Qgis.Info)

            bounds = "&boundary.rect.min_lon=" + str(dest_min_point.x()) + \
                     "&boundary.rect.min_lat=" + str(dest_min_point.y()) + \
                     "&boundary.rect.max_lon=" + str(dest_max_point.x()) + \
                     "&boundary.rect.max_lat=" + str(dest_max_point.y())
            search_URL = search_URL + bounds

        QgsMessageLog.logMessage(search_URL, "DigitransitGeocoder", Qgis.Info)

        request = QNetworkRequest()
        request.setUrl(QUrl(search_URL))

        self.network_access_manager.get(request)

    def handleSearchResponse(self, reply):
        error = reply.error()
        if error == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            data_string = str(bytes_string, 'utf-8')
            #QgsMessageLog.logMessage(data_string, "DigitransitGeocoder", Qgis.Info)

            self.listWidgetGeocodingResults.clear()

            geocoding_result = json.loads(data_string)

            self.features = []

            for feature in geocoding_result['features']:
                if feature['properties']['confidence'] >= self.horizontalSliderMinimumConfidenceValue.value() / 100:
                    self.listWidgetGeocodingResults.addItem(feature['properties']['label'])
                    self.features.append(feature)

        else:
            QgsMessageLog.logMessage(str(error), "DigitransitGeocoder", Qgis.Warning)
            QgsMessageLog.logMessage(reply.errorString(), "DigitransitGeocoder", Qgis.Warning)


        if len(self.features) > 0 and self.radioButtonResultsShowAll.isChecked():

            (layer, provider) = self.createSearchResultLayer()
            features = []

            for feature in self.features:
                qgs_feature = self.createFeature(feature)
                features.append(qgs_feature)

            provider.addFeatures(features)
            layer.commitChanges()
            QgsProject.instance().addMapLayer(layer)

    def handleSearchResultSelected(self, item):
        #QgsMessageLog.logMessage("Clicked item: " + str(item), "DigitransitGeocoder", Qgis.Info)
        #QgsMessageLog.logMessage("Clicked item text: " + str(item.text()), "DigitransitGeocoder", Qgis.Info)

        if len(self.features) > 0 and self.radioButtonResultsShowSelected.isChecked():
            (layer, provider) = self.createSearchResultLayer()
            selected_feature_index = self.listWidgetGeocodingResults.currentRow()
            feature = self.features[selected_feature_index]
            qgs_feature = self.createFeature(feature)
            provider.addFeature(qgs_feature)
            layer.commitChanges()
            QgsProject.instance().addMapLayer(layer)

    def createSearchResultLayer(self):
        layer = QgsVectorLayer("Point?crs=EPSG:4326", self.search_text + " layer", "memory")
        provider = layer.dataProvider()

        layer.startEditing()
        provider.addAttributes([QgsField("digitransit_id", QVariant.String),
                                QgsField("gid", QVariant.String),
                                QgsField("layer", QVariant.String),
                                QgsField("source", QVariant.String),
                                QgsField("source_id", QVariant.String),
                                QgsField("name", QVariant.String),
                                QgsField("postalcode", QVariant.Int),
                                QgsField("postalcode_gid", QVariant.String),
                                QgsField("confidence", QVariant.Double),
                                QgsField("accuracy", QVariant.String),
                                QgsField("country", QVariant.String),
                                QgsField("country_gid", QVariant.String),
                                QgsField("country_a", QVariant.String),
                                QgsField("region", QVariant.String),
                                QgsField("region_gid", QVariant.String),
                                QgsField("localadmin", QVariant.String),
                                QgsField("localadmin_gid", QVariant.String),
                                QgsField("locality", QVariant.String),
                                QgsField("locality_gid", QVariant.String),
                                QgsField("neighbourhood", QVariant.String),
                                QgsField("neighbourhood_gid", QVariant.String),
                                QgsField("label", QVariant.String)
                                ])

        return (layer, provider)

    def createFeature(self, feature):
        qgs_feature = QgsFeature()
        #QgsMessageLog.logMessage(str(feature), "DigitransitGeocoder", Qgis.Info)
        lon = feature['geometry']['coordinates'][0]
        lat = feature['geometry']['coordinates'][1]
        qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        properties = feature['properties']

        name = ''
        if 'name' in properties:
            name = properties['name']
        locality = ''
        locality_gid = ''
        if 'locality' in properties:
            locality = properties['locality']
            locality_gid = properties['locality_gid']
        neighbourhood = ''
        neighbourhood_gid = ''
        if 'neighbourhood' in properties:
            neighbourhood = properties['neighbourhood']
            neighbourhood_gid = properties['neighbourhood_gid']
        postalcode = ''
        postalcode_gid = ''
        if 'postalcode' in properties:
            postalcode = properties['postalcode']
            postalcode_gid = properties['postalcode_gid']
        country = ''
        country_gid = ''
        if 'country' in properties:
            country = properties['country']
            country_gid = properties['country_gid']
        country_a = ''
        if 'country_a' in properties:
            country_a = properties['country_a']
        region = ''
        region_gid = ''
        if 'region' in properties:
            region = properties['region']
            region_gid = properties['region_gid']
        localadmin = ''
        localadmin_gid = ''
        if 'localadmin' in properties:
            localadmin = properties['localadmin']
            localadmin_gid = properties['localadmin_gid']
        label = ''
        if 'label' in properties:
            label = properties['label']

        qgs_feature.setAttributes([properties['id'],
                                   properties['gid'],
                                   properties['layer'],
                                   properties['source'],
                                   properties['source_id'],
                                   name,
                                   postalcode,
                                   postalcode_gid,
                                   properties['confidence'],
                                   properties['accuracy'],
                                   country,
                                   country_gid,
                                   country_a,
                                   region,
                                   region_gid,
                                   localadmin,
                                   localadmin_gid,
                                   locality,
                                   locality_gid,
                                   neighbourhood,
                                   neighbourhood_gid,
                                   label
                                   ])

        return qgs_feature

    @pyqtSlot()
    def on_pushButtonReset_clicked(self):
        self.spinBoxMaxResults.setValue(DigitransitGeocoderDockWidget.DEFAULT_MAX_NUMBER_OF_RESULTS)
        self.checkBoxSearchMapCanvasArea.setChecked(DigitransitGeocoderDockWidget.DEFAULT_SEARCH_MAP_CANVAS_AREA)
        self.checkBoxNLS.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_NLS_DATA)
        self.checkBoxOA.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_OA_DATA)
        self.checkBoxOSM.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_OSM_DATA)
        self.checkBoxSearchAddress.setChecked(DigitransitGeocoderDockWidget.DEFAULT_SEARCH_ADDRESS)
        self.checkBoxSearchVenue.setChecked(DigitransitGeocoderDockWidget.DEFAULT_SEARCH_VENUE)
        self.checkBoxSearchStreet.setChecked(DigitransitGeocoderDockWidget.DEFAULT_SEARCH_STREET)
        self.horizontalSliderMinimumConfidenceValue.setValue(
            DigitransitGeocoderDockWidget.DEFAULT_MINIMUM_CONFIDENCE_VALUE * 100)
        self.radioButtonResultsShowAll.setChecked(DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP)
        self.radioButtonResultsShowSelected.setChecked(
            not DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP)

    @pyqtSlot(int)
    def on_spinBoxMaxResults_valueChanged(self, value):
        QSettings().setValue("/DigitransitGeocoder/maxNumberOfResults", value)

    def on_checkBoxSearchMapCanvasArea_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/searchMapCanvasArea", self.checkBoxSearchMapCanvasArea.isChecked())

    def on_checkBoxNLS_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/useNLSData", self.checkBoxNLS.isChecked())

    def on_checkBoxOA_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/useOAData", self.checkBoxOA.isChecked())

    def on_checkBoxOSM_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/useOSMData", self.checkBoxOSM.isChecked())

    def on_checkBoxSearchAddress_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/searchAddress", self.checkBoxSearchAddress.isChecked())

    def on_checkBoxSearchVenue_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/searchVenue", self.checkBoxSearchVenue.isChecked())

    def on_checkBoxSearchStreet_stateChanged(self):
        QSettings().setValue("/DigitransitGeocoder/searchStreet", self.checkBoxSearchStreet.isChecked())

    def on_horizontalSliderMinimumConfidenceValue_valueChanged(self):
        QSettings().setValue("/DigitransitGeocoder/minConfidenceValue",
                             self.horizontalSliderMinimumConfidenceValue.value())

    def on_radioButtonResultsShowAll_toggled(self):
        QSettings().setValue("/DigitransitGeocoder/showAllResultsOnMap", self.radioButtonResultsShowAll.isChecked())

    def on_radioButtonResultsShowSelected_toggled(self):
        QSettings().setValue("/DigitransitGeocoder/showSelectedResultOnMap",
                             self.radioButtonResultsShowSelected.isChecked())

    def tr(self, string):
        return QCoreApplication.translate('DigitransitGeocoderDockWidget', string)