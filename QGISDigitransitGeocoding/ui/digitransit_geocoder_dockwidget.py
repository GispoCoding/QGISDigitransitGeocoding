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

import json

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    QUrl,
    QVariant,
    pyqtSignal,
    pyqtSlot,
)
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from qgis.PyQt.QtWidgets import QMessageBox, QWidget

from ..qgis_plugin_tools.tools.resources import load_ui

# from qgis.utils import iface


FORM_CLASS: QWidget = load_ui("digitransit_geocoder_dockwidget_base.ui")


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

    closingPlugin = pyqtSignal()  # noqa N815

    def __init__(self, iface, parent=None):  # noqa QGS105
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
        # QMetaObject.connectSlotsByName(self)

        # Note this is not because we have the auto connection
        # self.pushButtonSearch.clicked.connect(self.handleSearch)

        self.network_access_manager = QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handle_search_response)

        self.listWidgetGeocodingResults.itemClicked.connect(
            self.handle_search_result_selected
        )

        self.spinBoxMaxResults.setValue(
            QSettings().value(
                "/QGISDigitransitGeocoding/maxNumberOfResults",
                DigitransitGeocoderDockWidget.DEFAULT_MAX_NUMBER_OF_RESULTS,
                type=int,
            )
        )
        self.checkBoxSearchMapCanvasArea.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/searchMapCanvasArea",
                DigitransitGeocoderDockWidget.DEFAULT_SEARCH_MAP_CANVAS_AREA,
                type=bool,
            )
        )
        self.checkBoxNLS.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/useNLSData",
                DigitransitGeocoderDockWidget.DEFAULT_USE_NLS_DATA,
                type=bool,
            )
        )
        self.checkBoxOA.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/useOAData",
                DigitransitGeocoderDockWidget.DEFAULT_USE_OA_DATA,
                type=bool,
            )
        )
        self.checkBoxOSM.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/useOSMData",
                DigitransitGeocoderDockWidget.DEFAULT_USE_OSM_DATA,
                type=bool,
            )
        )
        self.checkBoxSearchAddress.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/searchAddress",
                DigitransitGeocoderDockWidget.DEFAULT_SEARCH_ADDRESS,
                type=bool,
            )
        )
        self.checkBoxSearchVenue.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/searchVenue",
                DigitransitGeocoderDockWidget.DEFAULT_SEARCH_VENUE,
                type=bool,
            )
        )
        self.checkBoxSearchStreet.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/searchStreet",
                DigitransitGeocoderDockWidget.DEFAULT_SEARCH_STREET,
                type=bool,
            )
        )
        self.horizontalSliderMinimumConfidenceValue.setValue(
            QSettings().value(
                "/QGISDigitransitGeocoding/minConfidenceValue",
                DigitransitGeocoderDockWidget.DEFAULT_MINIMUM_CONFIDENCE_VALUE * 100,
                type=int,
            )
        )
        self.radioButtonResultsShowAll.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/showAllResultsOnMap",
                DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP,
                type=bool,
            )
        )
        self.radioButtonResultsShowSelected.setChecked(
            QSettings().value(
                "/QGISDigitransitGeocoding/showSelectedResultOnMap",
                not DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP,
                type=bool,
            )
        )

    def close_event(self, event):
        self.closingPlugin.emit()
        event.accept()

    # Without this the signal is handled twice, see
    # https://stackoverflow.com/questions/14311578/event-signal-is-emmitted-twice-every-time
    @pyqtSlot()
    def on_pushbuttonsearch_clicked(self):
        self.search_text = self.lineEditAddress.text()
        if len(self.search_text) == 0:
            return
        self.geocode(self.search_text)

    def geocode(self, search_text):
        base_url = "http://api.digitransit.fi/geocoding/v1/search"
        size = self.spinBoxMaxResults.value()
        search_url = base_url + "?text=" + search_text + "&size=" + str(size)

        if (
            self.checkBoxNLS.isChecked()
            or self.checkBoxOA.isChecked()
            or self.checkBoxOSM.isChecked()
        ):
            sources = "&sources="
            if self.checkBoxNLS.isChecked():
                sources = sources + "nlsfi,"
            if self.checkBoxOA.isChecked():
                sources = sources + "oa,"
            if self.checkBoxOSM.isChecked():
                sources = sources + "osm,"
            search_url = search_url + sources.rstrip(",")
        else:
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("No data sources selected"),
                self.tr("Please, select at least one data source"),
            )
            return

        if (
            self.checkBoxSearchAddress.isChecked()
            or self.checkBoxSearchVenue.isChecked()
            or self.checkBoxSearchStreet.isChecked()
        ):
            layers = "&layers="
            if self.checkBoxSearchAddress.isChecked():
                layers = layers + "address,"
            if self.checkBoxSearchVenue.isChecked():
                layers = layers + "venue,"
            if self.checkBoxSearchStreet.isChecked():
                layers = layers + "street,"
            search_url = search_url + layers.rstrip(",")
        else:
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("No types of locations selected"),
                self.tr("Please, select at least one type of location to search"),
            )
            return

        if self.checkBoxSearchMapCanvasArea.isChecked():
            extent = self.iface.mapCanvas().extent()  # QgsRectangle
            min_lon = extent.xMinimum()
            min_lat = extent.yMinimum()
            max_lon = extent.xMaximum()
            max_lat = extent.yMaximum()

            source_crs = QgsProject.instance().crs()
            dest_crs = QgsCoordinateReferenceSystem(4326)
            transform = QgsCoordinateTransform(
                source_crs, dest_crs, QgsProject.instance()
            )
            dest_min_point = transform.transform(QgsPointXY(min_lon, min_lat))
            dest_max_point = transform.transform(QgsPointXY(max_lon, max_lat))

            bounds = (
                "&boundary.rect.min_lon="
                + str(dest_min_point.x())
                + "&boundary.rect.min_lat="
                + str(dest_min_point.y())
                + "&boundary.rect.max_lon="
                + str(dest_max_point.x())
                + "&boundary.rect.max_lat="
                + str(dest_max_point.y())
            )
            search_url = search_url + bounds

        QgsMessageLog.logMessage(search_url, "QGISDigitransitGeocoding", Qgis.Info)

        request = QNetworkRequest()
        request.setUrl(QUrl(search_url))

        self.network_access_manager.get(request)

    def handle_search_response(self, reply):
        error = reply.error()
        if error == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            data_string = str(bytes_string, "utf-8")

            self.listWidgetGeocodingResults.clear()

            geocoding_result = json.loads(data_string)

            self.features = []

            for feature in geocoding_result["features"]:
                if (
                    feature["properties"]["confidence"]
                    >= self.horizontalSliderMinimumConfidenceValue.value() / 100
                ):
                    self.listWidgetGeocodingResults.addItem(
                        feature["properties"]["label"]
                    )
                    self.features.append(feature)

        else:
            QgsMessageLog.logMessage(
                str(error), "QGISDigitransitGeocoding", Qgis.Warning
            )
            QgsMessageLog.logMessage(
                reply.errorString(), "QGISDigitransitGeocoding", Qgis.Warning
            )

        if len(self.features) > 0 and self.radioButtonResultsShowAll.isChecked():

            (layer, provider) = self.create_search_result_layer()
            features = []

            for feature in self.features:
                qgs_feature = self.create_feature(feature)
                features.append(qgs_feature)

            provider.addFeatures(features)
            layer.commitChanges()
            QgsProject.instance().addMapLayer(layer)

    def handle_search_result_selected(self, item):

        if len(self.features) > 0 and self.radioButtonResultsShowSelected.isChecked():
            (layer, provider) = self.create_search_result_layer()
            selected_feature_index = self.listWidgetGeocodingResults.currentRow()
            feature = self.features[selected_feature_index]
            qgs_feature = self.create_feature(feature)
            provider.addFeature(qgs_feature)
            layer.commitChanges()
            QgsProject.instance().addMapLayer(layer)

    def create_search_result_layer(self):
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326", self.search_text + " layer", "memory"
        )
        provider = layer.dataProvider()

        layer.startEditing()
        provider.addAttributes(
            [
                QgsField("digitransit_id", QVariant.String),
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
                QgsField("label", QVariant.String),
            ]
        )

        return (layer, provider)

    def create_feature(self, feature):
        qgs_feature = QgsFeature()
        lon = feature["geometry"]["coordinates"][0]
        lat = feature["geometry"]["coordinates"][1]
        qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        properties = feature["properties"]

        name = ""
        if "name" in properties:
            name = properties["name"]
        locality = ""
        locality_gid = ""
        if "locality" in properties:
            locality = properties["locality"]
            locality_gid = properties["locality_gid"]
        neighbourhood = ""
        neighbourhood_gid = ""
        if "neighbourhood" in properties:
            neighbourhood = properties["neighbourhood"]
            neighbourhood_gid = properties["neighbourhood_gid"]
        postalcode = ""
        postalcode_gid = ""
        if "postalcode" in properties:
            postalcode = properties["postalcode"]
            postalcode_gid = properties["postalcode_gid"]
        country = ""
        country_gid = ""
        if "country" in properties:
            country = properties["country"]
            country_gid = properties["country_gid"]
        country_a = ""
        if "country_a" in properties:
            country_a = properties["country_a"]
        region = ""
        region_gid = ""
        if "region" in properties:
            region = properties["region"]
            region_gid = properties["region_gid"]
        localadmin = ""
        localadmin_gid = ""
        if "localadmin" in properties:
            localadmin = properties["localadmin"]
            localadmin_gid = properties["localadmin_gid"]
        label = ""
        if "label" in properties:
            label = properties["label"]

        qgs_feature.setAttributes(
            [
                properties["id"],
                properties["gid"],
                properties["layer"],
                properties["source"],
                properties["source_id"],
                name,
                postalcode,
                postalcode_gid,
                properties["confidence"],
                properties["accuracy"],
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
                label,
            ]
        )

        return qgs_feature

    @pyqtSlot()
    def on_pushbutton_reset_clicked(self):
        self.spinBoxMaxResults.setValue(
            DigitransitGeocoderDockWidget.DEFAULT_MAX_NUMBER_OF_RESULTS
        )
        self.checkBoxSearchMapCanvasArea.setChecked(
            DigitransitGeocoderDockWidget.DEFAULT_SEARCH_MAP_CANVAS_AREA
        )
        self.checkBoxNLS.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_NLS_DATA)
        self.checkBoxOA.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_OA_DATA)
        self.checkBoxOSM.setChecked(DigitransitGeocoderDockWidget.DEFAULT_USE_OSM_DATA)
        self.checkBoxSearchAddress.setChecked(
            DigitransitGeocoderDockWidget.DEFAULT_SEARCH_ADDRESS
        )
        self.checkBoxSearchVenue.setChecked(
            DigitransitGeocoderDockWidget.DEFAULT_SEARCH_VENUE
        )
        self.checkBoxSearchStreet.setChecked(
            DigitransitGeocoderDockWidget.DEFAULT_SEARCH_STREET
        )
        self.horizontalSliderMinimumConfidenceValue.setValue(
            DigitransitGeocoderDockWidget.DEFAULT_MINIMUM_CONFIDENCE_VALUE * 100
        )
        self.radioButtonResultsShowAll.setChecked(
            DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP
        )
        self.radioButtonResultsShowSelected.setChecked(
            not DigitransitGeocoderDockWidget.DEFAULT_SHOW_ALL_RESULTS_ON_MAP
        )

    @pyqtSlot(int)
    def on_spinbox_max_results_value_changed(self, value):
        QSettings().setValue("/QGISDigitransitGeocoding/maxNumberOfResults", value)

    def on_checkbox_search_mapcanvas_area_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/searchMapCanvasArea",
            self.checkBoxSearchMapCanvasArea.isChecked(),
        )

    def on_checkbox_nls_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/useNLSData", self.checkBoxNLS.isChecked()
        )

    def on_checkbox_oa_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/useOAData", self.checkBoxOA.isChecked()
        )

    def on_checkbox_osm_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/useOSMData", self.checkBoxOSM.isChecked()
        )

    def on_checkbox_search_address_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/searchAddress",
            self.checkBoxSearchAddress.isChecked(),
        )

    def on_checkbox_search_venue_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/searchVenue",
            self.checkBoxSearchVenue.isChecked(),
        )

    def on_checkbox_search_street_state_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/searchStreet",
            self.checkBoxSearchStreet.isChecked(),
        )

    def on_horizontalslider_minimum_confidence_value_changed(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/minConfidenceValue",
            self.horizontalSliderMinimumConfidenceValue.value(),
        )

    def on_radiobutton_results_showall_toggled(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/showAllResultsOnMap",
            self.radioButtonResultsShowAll.isChecked(),
        )

    def on_radiobutton_results_showselected_toggled(self):
        QSettings().setValue(
            "/QGISDigitransitGeocoding/showSelectedResultOnMap",
            self.radioButtonResultsShowSelected.isChecked(),
        )

    def tr(self, string):
        return QCoreApplication.translate("DigitransitGeocoderDockWidget", string)
