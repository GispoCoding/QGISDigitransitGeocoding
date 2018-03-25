# digitransit_geocoder_processing_plugin_algorithm.py
#
# Created
#  by Erno Mäkinen (erno@gispo.fi)
#  on 24.3.2018

import json
import urllib
import urllib.parse

from PyQt5.QtCore import (QCoreApplication,
                          QVariant)


from qgis.core import (QgsProcessing,
    QgsFeatureSink,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
    QgsWkbTypes,
    QgsProcessingParameterFeatureSink,
    Qgis,
    QgsMessageLog,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsCoordinateReferenceSystem,
    QgsVectorLayer,
    QgsGeometry,
    QgsPointXY)


class DigitransitGeocoderPluginAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SEPARATOR = 'SEPARATOR'
    ADDRESS_FIELD_NAMES = 'ADDRESS_FIELD_NAMES'
    address_field_indices = []

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Input CSV file'),
                extension='csv'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.SEPARATOR,
                self.tr('Column separator'),
                ';'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.ADDRESS_FIELD_NAMES,
                self.tr('Address field name(s) as a comma separated list'),
                'Laitoksen sijaintiosoite, Laitoksen sijaintikunta'
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        self.feedback = feedback

        col_separator = self.parameterAsString(parameters, self.SEPARATOR, context)
        address_field_names_string = self.parameterAsString(parameters, self.ADDRESS_FIELD_NAMES, context)

        file_path = self.parameterAsFile(parameters, self.INPUT, context)

        # QgsMessageLog.logMessage(str(file_path), "DigitransitGeocoder", Qgis.Info)

        try:
            with open(file_path, 'r') as csv_file:

                address_field_name_tokens = address_field_names_string.split(',')
                address_field_names = []
                for address_field_name_token in address_field_name_tokens:
                    address_field_name = address_field_name_token.lstrip(' ').rstrip(' ')
                    address_field_names.append(address_field_name)

                # Use the header row for feature field names
                header_row = next(csv_file)
                columns = header_row.rstrip().split(col_separator)
                # QgsMessageLog.logMessage(str(columns), "DigitransitGeocoder", Qgis.Info)
                fields = QgsFields()
                for column in columns:
                    fields.append(QgsField(column, QVariant.String))

                    for index, address_field_name in enumerate(address_field_names):
                        if column == address_field_name:
                            self.address_field_indices.append(index)
                            break

                # Add the Digitransit.fi
                fields.append(QgsField("digitransit_confidence", QVariant.Double))
                fields.append(QgsField("digitransit_accuracy", QVariant.String))
                fields.append(QgsField("digitransit_layer", QVariant.String))
                fields.append(QgsField("digitransit_source", QVariant.String))
                fields.append(QgsField("digitransit_name", QVariant.String))
                fields.append(QgsField("digitransit_localadmin", QVariant.String))
                fields.append(QgsField("digitransit_locality", QVariant.String))
                fields.append(QgsField("digitransit_postalcode", QVariant.Int))
                fields.append(QgsField("digitransit_region", QVariant.String))
                fields.append(QgsField("digitransit_digitransit_query", QVariant.String))

                # QgsMessageLog.logMessage(str(fields.toList()), "DigitransitGeocoder", Qgis.Info)
                # QgsMessageLog.logMessage(str(QgsWkbTypes.Point), "DigitransitGeocoder", Qgis.Info)

                self.layer = QgsVectorLayer("Point?crs=EPSG:4326", "geocoding result layer", "memory")
                self.provider = self.layer.dataProvider()
                self.layer.startEditing()
                self.provider.addAttributes(fields)
                self.features = []

                (self.sink, self.dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                                                                 context, fields, QgsWkbTypes.Point,
                                                                 QgsCoordinateReferenceSystem(4326))

                # QgsMessageLog.logMessage("Created sink", "DigitransitGeocoder", Qgis.Info)

                self.csv_rows = []

                for row in csv_file:
                    values = row.strip('\n').split(col_separator)
                    # QgsMessageLog.logMessage(str(values), "DigitransitGeocoder", Qgis.Info)

                    self.csv_rows.append(values)

                self.geocode_csv_rows(self.csv_rows)

        except IOError as e:
            QgsMessageLog.logMessage(str(e), "DigitransitGeocoder", Qgis.Critical)

        return {self.OUTPUT: self.dest_id}

    def geocode_csv_rows(self, rows):
        self.total_geocode_count = len(rows)
        self.geocode_count = 0

        for row in rows:

            # Create search text (address) based on the address fields specified by the user
            address = ''
            for index in self.address_field_indices:
                address += row[index] + ","
            address = address.rstrip(",")

            base_URL = "http://api.digitransit.fi/geocoding/v1/search?"

            search_parameters = {
                'text': address,
                # 'sources': 'oa',
                'size': 50
            }

            query_string = urllib.parse.urlencode(search_parameters)

            search_URL = base_URL + query_string

            QgsMessageLog.logMessage(search_URL, "DigitransitGeocoder", Qgis.Info)

            r = urllib.request.urlopen(search_URL)
            geocoding_result = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
            # QgsMessageLog.logMessage(str(geocoding_result), "DigitransitGeocoder", Qgis.Info)

            if self.feedback.isCanceled():
                return

            self.geocode_count += 1

            if len(geocoding_result['features']) > 0:
                feature = geocoding_result['features'][0]  # We use only the feature with the highest confidence value
            else:
                QgsMessageLog.logMessage("Geocode not succesful for address: " + address, "DigitransitGeocoder",
                                         Qgis.Warning)
                return

            qgs_feature = QgsFeature()
            lon = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]
            qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))

            values = list(row)

            # also add a few of the geocoding result feature properties if available
            properties = feature['properties']
            confidence = -1
            if 'confidence' in properties:
                confidence = properties['confidence']
            values.append(confidence)
            accuracy = ''
            if 'accuracy' in properties:
                accuracy = properties['accuracy']
            values.append(accuracy)
            layer = ''
            if 'layer' in properties:
                layer = properties['layer']
            values.append(layer)
            source = ''
            if 'source' in properties:
                source = properties['source']
            values.append(source)
            name = ''
            if 'name' in properties:
                name = properties['name']
            values.append(name)
            localadmin = ''
            if 'localadmin' in properties:
                localadmin = properties['localadmin']
            values.append(localadmin)
            locality = ''
            if 'locality' in properties:
                locality = properties['locality']
            values.append(locality)
            postalcode = -1
            if 'postalcode' in properties:
                postalcode = properties['postalcode']
            values.append(postalcode)
            region = ''
            if 'region' in properties:
                region = properties['region']
            values.append(region)
            values.append(search_URL)

            qgs_feature.setAttributes(values)

            # Add a feature in the sink
            self.sink.addFeature(qgs_feature, QgsFeatureSink.FastInsert)

            # QgsMessageLog.logMessage("Added a feature", "DigitransitGeocode    r", Qgis.Info)

            # Update the progress bar
            self.feedback.setProgress(int(self.geocode_count * (100.0 / self.total_geocode_count)))

            if self.geocode_count == self.total_geocode_count:
                QgsMessageLog.logMessage("Finished geocoding the CSV file", "DigitransitGeocoder", Qgis.Info)

    def name(self):
        return 'geocodecsv'

    def displayName(self):
        return self.tr('Geocode addresses in a CSV file')

    def group(self):
        return self.tr('Geocode')

    def groupId(self):
        return 'geocoding'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DigitransitGeocoderPluginAlgorithm()
