# digitransit_geocoder_processing_plugin_algorithm.py
#
# Created
#  by Erno Mäkinen (erno@gispo.fi)
#  on 24.3.2018

import json
import urllib
import urllib.parse
from pathlib import Path
import os

from PyQt5.QtCore import (QCoreApplication,
                          QVariant)

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber,
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


class DigitransitGeocoderPluginAlgorithmError(Exception):
    pass


class DigitransitGeocoderPluginAlgorithm(QgsProcessingAlgorithm):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    SEPARATOR = 'SEPARATOR'
    ADDRESS_FIELD_NAMES = 'ADDRESS_FIELD_NAMES'

    SEARCH_EXTENT = 'SEARCH_EXTENT'

    SOURCE_OSM = 'SOURCE_OSM'
    SOURCE_OA = 'SOURCE_OA'
    SOURCE_NLS = 'SOURCE_NLS'

    MAX_NUMBER_OF_SEARCH_RESULTS = 'MAX_NUMBER_OF_SEARCH_RESULTS'
    MAX_NUMBER_OF_SEARCH_RESULT_ROWS = 'MAX_NUMBER_OF_SEARCH_RESULT_ROWS'

    LOCATION_TYPE_STREET = 'LOCATION_TYPE_STREET'
    LOCATION_TYPE_VENUE = 'LOCATION_TYPE_VENUE'
    LOCATION_TYPE_ADDRESS = 'LOCATION_TYPE_ADDRESS'

    address_field_indices = []

    def initAlgorithm(self, config=None):

        self.translator = None

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

        default_address_value = self.tr('For example: street address, municipality')
        self.addParameter(
            QgsProcessingParameterString(
                self.ADDRESS_FIELD_NAMES,
                self.tr('Address field name(s) as a comma separated list'),
                default_address_value
            )
        )

        self.addParameter(
            QgsProcessingParameterExtent(
                self.SEARCH_EXTENT,
                self.tr('Extent of the search area, in EPSG:4326 if unspecified'),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SOURCE_OA,
                self.tr('Use OpenAddress DB as a data source'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SOURCE_OSM,
                self.tr('Use OpenStreetMap as a data source'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SOURCE_NLS,
                self.tr('Use National Land Survey places as a data source'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_NUMBER_OF_SEARCH_RESULTS,
                self.tr('Number of the locations to search (may affect also result accuracy)'),
                defaultValue=10,
                minValue=1,
                maxValue=40
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_NUMBER_OF_SEARCH_RESULT_ROWS,
                self.tr('Max number of result rows per CSV row (<= number of the locations to search)'),
                defaultValue=1,
                minValue=1,
                maxValue=40
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOCATION_TYPE_STREET,
                self.tr('Search streets'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOCATION_TYPE_VENUE,
                self.tr('Search venues'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOCATION_TYPE_ADDRESS,
                self.tr('Search addresses'),
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        self.parameters = parameters
        self.context = context
        self.feedback = feedback

        col_separator = self.parameterAsString(parameters, self.SEPARATOR, context)
        address_field_names_string = self.parameterAsString(parameters, self.ADDRESS_FIELD_NAMES, context)

        extent = self.parameterAsExtent(parameters, self.SEARCH_EXTENT, context,
                                        QgsCoordinateReferenceSystem(4326))  # QgsRectangle
        # QgsMessageLog.logMessage(str(extent), "DigitransitGeocoder", Qgis.Info)

        min_lon = extent.xMinimum()
        min_lat = extent.yMinimum()
        max_lon = extent.xMaximum()
        max_lat = extent.yMaximum()
        #QgsMessageLog.logMessage(str(min_lon), "DigitransitGeocoder", Qgis.Info)
        #QgsMessageLog.logMessage(str(min_lat), "DigitransitGeocoder", Qgis.Info)
        #QgsMessageLog.logMessage(str(max_lon), "DigitransitGeocoder", Qgis.Info)
        #QgsMessageLog.logMessage(str(max_lat), "DigitransitGeocoder", Qgis.Info)

        if min_lon < max_lon and min_lat < max_lat:
            self.bounds = "&boundary.rect.min_lon=" + str(min_lon) + \
                     "&boundary.rect.min_lat=" + str(min_lat) + \
                     "&boundary.rect.max_lon=" + str(max_lon) + \
                     "&boundary.rect.max_lat=" + str(max_lat)
        else:
            self.bounds = None

        self.use_source_OA = self.parameterAsBool(parameters, self.SOURCE_OA, context)
        self.use_source_OSM = self.parameterAsBool(parameters, self.SOURCE_OSM, context)
        self.use_source_NLS = self.parameterAsBool(parameters, self.SOURCE_NLS, context)

        self.max_n_of_search_results = self.parameterAsInt(parameters, self.MAX_NUMBER_OF_SEARCH_RESULTS, context)
        max_n_of_search_result_rows = self.parameterAsInt(parameters, self.MAX_NUMBER_OF_SEARCH_RESULT_ROWS, context)
        self.max_n_of_search_result_rows = \
            max_n_of_search_result_rows \
                if max_n_of_search_result_rows <= self.max_n_of_search_results \
                else self.max_n_of_search_results


        self.use_location_type_street = self.parameterAsBool(parameters, self.LOCATION_TYPE_STREET, context)
        self.use_location_type_venue = self.parameterAsBool(parameters, self.LOCATION_TYPE_VENUE, context)
        self.use_location_type_address = self.parameterAsBool(parameters, self.LOCATION_TYPE_ADDRESS, context)

        file_path = self.parameterAsFile(parameters, self.INPUT, context)

        # QgsMessageLog.logMessage(str(file_path), "DigitransitGeocoder", Qgis.Info)

        try:
            self.feedback.pushInfo(
                self.tr("Trying to read the CSV file in UTF-8 format."))
            self.read_csv_data(file_path, 'utf-8', col_separator, address_field_names_string)
        except DigitransitGeocoderPluginAlgorithmError as e:
            QgsMessageLog.logMessage(type(e).__name__ + ': ' + str(e), "DigitransitGeocoder", Qgis.Critical)
            return { self.OUTPUT: None }

        self.geocode_csv_rows(self.csv_rows)

        return {self.OUTPUT: self.dest_id}

    def read_csv_data(self, file_path, file_encoding, col_separator, address_field_names_string):

        # Let's try to use csvt-file (see https://giswiki.hsr.ch/GeoCSV) if one exists
        col_data_types = []
        try:
            with open(file_path + 't', 'r', encoding=file_encoding) as csvt_file:
                types_row = next(csvt_file)
                types_tokens = types_row.rstrip().split(',')
                for type_token in types_tokens:
                    col_data_types.append(type_token.strip(' ').strip('"').lower())
        except IOError as e:
            if not Path(file_path + 't').exists():
                self.feedback.pushInfo(
                    self.tr(
                        "No CSVT file present, using the string type for all columns."))
                QgsMessageLog.logMessage(
                    self.tr("No CSVT file present, using the string type for all columns."),
                    "DigitransitGeocoder", Qgis.Info)
            else:
                self.feedback.pushInfo(
                    self.tr(
                        "Error while accessing the CSVT file, using the string type for all columns."))
                QgsMessageLog.logMessage(
                    self.tr("Error while accessing the CSVT file, using the string type for all columns."),
                    "DigitransitGeocoder",
                    Qgis.Warning)

        # QgsMessageLog.logMessage(str(col_data_types), "DigitransitGeocoder", Qgis.Info)

        try:
            with open(file_path, 'r', encoding=file_encoding) as csv_file:

                address_field_name_tokens = address_field_names_string.split(',')
                address_field_names = []
                for address_field_name_token in address_field_name_tokens:
                    address_field_name = address_field_name_token.lstrip(' ').rstrip(' ')
                    address_field_names.append(address_field_name)

                # Use the header row for feature field names
                header_row = next(csv_file)
                header_columns = header_row.rstrip().split(col_separator)

                if len(header_columns) == 1:
                    self.feedback.pushInfo(
                        self.tr("Using the separator ") + col_separator + self.tr(" and there is only one column in the CSV file."))

                header_columns = self.checkHeader(header_columns, address_field_names)

                # QgsMessageLog.logMessage(str(columns), "DigitransitGeocoder", Qgis.Info)
                # QgsMessageLog.logMessage("len(col_data_types):" + str(len(col_data_types)), "DigitransitGeocoder", Qgis.Info)
                # QgsMessageLog.logMessage("len(columns):" + str(len(columns)), "DigitransitGeocoder", Qgis.Info)

                if len(col_data_types) > 0 and len(col_data_types) != len(header_columns):
                    self.feedback.pushInfo(
                       self.tr("CSVT file present but it has different count of columns than the CSV file, using the string type."))
                    QgsMessageLog.logMessage(
                        self.tr(
                            "CSVT file present but it has different count of columns than the CSV file, using the string type for all columns."),
                        "DigitransitGeocoder", Qgis.Warning)
                # QgsMessageLog.logMessage(str(columns), "DigitransitGeocoder", Qgis.Info)
                fields = QgsFields()
                for index, column in enumerate(header_columns):
                    if len(col_data_types) == len(header_columns):
                        self.add_layer_data_field_with_type(index, col_data_types, column, fields)
                    else:
                        fields.append(QgsField(column, QVariant.String))

                    for address_field_name in address_field_names:
                        if column == address_field_name:
                            self.address_field_indices.append(index)
                            break

                # Add the Digitransit.fi
                fields.append(QgsField("digitransit_id", QVariant.String))
                fields.append(QgsField("digitransit_gid", QVariant.String))
                fields.append(QgsField("digitransit_confidence", QVariant.Double))
                fields.append(QgsField("digitransit_accuracy", QVariant.String))
                fields.append(QgsField("digitransit_layer", QVariant.String))
                fields.append(QgsField("digitransit_source", QVariant.String))
                fields.append(QgsField("digitransit_source_id", QVariant.String))
                fields.append(QgsField("digitransit_name", QVariant.String))
                fields.append(QgsField("digitransit_localadmin", QVariant.String))
                fields.append(QgsField("digitransit_localadmin_gid", QVariant.String))
                fields.append(QgsField("digitransit_locality", QVariant.String))
                fields.append(QgsField("digitransit_locality_gid", QVariant.String))
                fields.append(QgsField("digitransit_postalcode", QVariant.Int))
                fields.append(QgsField("digitransit_postalcode_gid", QVariant.String))
                fields.append(QgsField("digitransit_region", QVariant.String))
                fields.append(QgsField("digitransit_region_gid", QVariant.String))
                fields.append(QgsField("digitransit_country", QVariant.String))
                fields.append(QgsField("digitransit_country_gid", QVariant.String))
                fields.append(QgsField("digitransit_country_a", QVariant.String))
                fields.append(QgsField("digitransit_neighbourhood", QVariant.String))
                fields.append(QgsField("digitransit_neighbourhood_gid", QVariant.String))
                fields.append(QgsField("digitransit_label", QVariant.String))
                fields.append(QgsField("digitransit_query", QVariant.String))


                # QgsMessageLog.logMessage(str(fields.toList()), "DigitransitGeocoder", Qgis.Info)
                # QgsMessageLog.logMessage(str(QgsWkbTypes.Point), "DigitransitGeocoder", Qgis.Info)

                (self.sink, self.dest_id) = self.parameterAsSink(self.parameters, self.OUTPUT,
                                                                 self.context, fields, QgsWkbTypes.Point,
                                                                 QgsCoordinateReferenceSystem(4326))

                # QgsMessageLog.logMessage("Created sink", "DigitransitGeocoder", Qgis.Info)

                self.csv_rows = []

                for row_index, row in enumerate(csv_file):
                    values = row.strip('\n').split(col_separator)
                    # QgsMessageLog.logMessage(str(values), "DigitransitGeocoder", Qgis.Info)
                    if len(values) != len(header_columns):
                        self.feedback.pushInfo(
                            self.tr("The CSV row ") + \
                                str(row_index + 1) + \
                                self.tr(" does not have same count of columns as the header row, skipping this row."))
                        QgsMessageLog.logMessage(
                            self.tr("The CSV row ") + \
                                    str(row_index + 1) + \
                                    self.tr(" does not have same count of columns as the header row, skipping this row."),
                            "DigitransitGeocoder",
                            Qgis.Warning)
                    else:
                        self.csv_rows.append(values)
        except IOError as e:
            QgsMessageLog.logMessage(type(e).__name__ + ': ' + str(e), "DigitransitGeocoder", Qgis.Critical)
            self.feedback.reportError(
                self.tr("Cannot read the CSV file."))
            raise DigitransitGeocoderPluginAlgorithmError()
        except UnicodeDecodeError as e:
            QgsMessageLog.logMessage(type(e).__name__ + ': ' + str(e), "DigitransitGeocoder", Qgis.Info)
            try:
                self.feedback.pushInfo(
                    self.tr("Trying to read the CSV file in ISO-8859-1 format."))
                self.read_csv_data(file_path, 'iso-8859-1', col_separator, address_field_names_string)
            except IOError as e:
                QgsMessageLog.logMessage(type(e).__name__ + ': ' + str(e), "DigitransitGeocoder", Qgis.Critical)
                self.feedback.reportError(
                    self.tr("Cannot read the CSV file."))
                raise DigitransitGeocoderPluginAlgorithmError()
            except UnicodeDecodeError as e:
                QgsMessageLog.logMessage(self.tr('Please, provide the CSV file in UTF-8 or ISO-8859-1 format.'), "DigitransitGeocoder", Qgis.Critical)
                # QMessageBox.critical(
                #     qgis.utils.iface,
                #     self.tr('Unknown CSV file encoding'),
                #     self.tr('Please, provide the CSV file in UTF-8 or ISO-8859-1 format.'))
                self.feedback.reportError(self.tr("Unknown CSV file encoding. Please, provide the CSV file in UTF-8 or ISO-8859-1 format."))
                raise DigitransitGeocoderPluginAlgorithmError()

    def checkHeader(self, header_columns, address_field_names):
        '''
        Validity checks for the header including user specified header related information.
        '''

        checked_header_columns = []

        if len(header_columns) != len(set(header_columns)):
            self.feedback.pushInfo(
                self.tr("Header has columns with equal names, adding an extra identifier in a column name."))
            QgsMessageLog.logMessage(
                self.tr("Header has columns with equal names, adding an extra identifier in a column name."),
                "DigitransitGeocoder", Qgis.Warning)
            # self.iface.messageBar().pushMessage(
            #    self.tr("CSV header"),
            #    self.tr("Header has columns with equal names, adding an extra identifier."),
            #    QgsMessageBar.WARNING,
            #    10)

            for i, col1 in enumerate(header_columns):
                found = False
                for j, col2 in enumerate(header_columns[(i + 1):]):
                    if col1 == col2:
                        found = True
                        break
                if found:
                    checked_header_columns.append(col1 + '_' + str(i + 1))
                else:
                    checked_header_columns.append(col1)
        else:
            checked_header_columns = header_columns

        for address_field_name in address_field_names:
            found = False
            for header_column in checked_header_columns:
                if address_field_name == header_column:
                    found = True
                    break
            if not found:
                QgsMessageLog.logMessage(self.tr('An address field name that you specified is not in the CSV headers.'),
                                         "DigitransitGeocoder", Qgis.Critical)
                # QMessageBox.critical(
                #     qgis.utils.iface,
                #     self.tr('Address field name error'),
                #     self.tr('An address field name that you specified is not in the CSV headers.'))
                self.feedback.reportError(
                    self.tr("An address field name that you specified is not in the CSV headers."))
                raise DigitransitGeocoderPluginAlgorithmError()

        return checked_header_columns

    def add_layer_data_field_with_type(self, index, header_column_data_types, header_column, fields):
        '''
        Creates and adds QgsField object with string or possibly specified other data type to the fields that define
        the vector layer (sink) feature attribute types.
        '''
        col_data_type = header_column_data_types[index]
        if col_data_type.startswith('string'):
            length = 255

            if col_data_type != 'string':
                success = True
                start = col_data_type.find('(') + 1
                if start != -1:
                    end = col_data_type.find(')', start)
                    if end != -1:
                        try:
                            length = int(col_data_type[start:end])
                        except ValueError:
                            success = False
                    else:
                        success = False
                else:
                    success = False

                if not success:
                    self.feedback.pushInfo(
                        self.tr("CSVT file has column that has unknown type: ") + \
                        header_column_data_types[index] + self.tr(", using the string type."))
                    QgsMessageLog.logMessage(self.tr("CSVT file has column that has unknown type: ") + \
                                             header_column_data_types[index] + self.tr(", using the string type."),
                                             "DigitransitGeocoder", Qgis.Warning)

            fields.append(QgsField(header_column, QVariant.String, len=length))

        elif col_data_type.startswith('integer'):
            length = -1

            if col_data_type != 'integer':
                success = True
                start = col_data_type.find('(') + 1
                if start != -1:
                    end = col_data_type.find(')', start)
                    if end != -1:
                        if col_data_type[start:end] == 'boolean' or col_data_type[start:end].startswith('int'):
                            self.feedback.pushInfo(
                                self.tr("Integer subtypes not supported, using the general integer type."))
                            QgsMessageLog.logMessage(
                                self.tr("Integer subtypes not supported, using the general integer type."),
                                "DigitransitGeocoder", Qgis.Warning)
                            fields.append(QgsField(header_column, QVariant.Int, len=length))
                        else:
                            try:
                                length = int(col_data_type[start:end])
                            except ValueError:
                                success = False
                    else:
                        success = False
                else:
                    success = False

                if not success:
                    self.feedback.pushInfo(
                        self.tr("CSVT file has column that has unknown type: ") + \
                        header_column_data_types[index] + self.tr(", using the string type."))
                    QgsMessageLog.logMessage(self.tr("CSVT file has column that has unknown type: ") + \
                                             header_column_data_types[index] + self.tr(", using the string type."),
                                             "DigitransitGeocoder", Qgis.Warning)
                    fields.append(QgsField(header_column, QVariant.String))
                else:
                    fields.append(QgsField(header_column, QVariant.Int, len=length))
            else:
                fields.append(QgsField(header_column, QVariant.Int, len=length))

        elif col_data_type.startswith('real'):
            length = 20
            precision = 5

            if col_data_type != 'real':
                success = True
                start = col_data_type.find('(') + 1
                if start != -1:
                    end = col_data_type.find(')', start)
                    if end != -1:
                        if col_data_type[start:end].startswith('float'):
                            self.feedback.pushInfo(
                                self.tr(
                                    "Real subtypes not supported, using the general real type with length 20, precision 5."))
                            QgsMessageLog.logMessage(
                                self.tr(
                                    "Real subtypes not supported, using the general real type with length 20, precision 5."),
                                "DigitransitGeocoder", Qgis.Warning)
                            fields.append(QgsField(header_column, QVariant.Double, len=length))
                        else:
                            try:
                                col_data_type_tokens = col_data_type[start:end].split('.')
                                length = int(col_data_type_tokens[0])
                                precision = int(col_data_type_tokens[1])
                            except ValueError:
                                success = False
                    else:
                        success = False
                else:
                    success = False

                if not success:
                    self.feedback.pushInfo(
                        self.tr("CSVT file has column that has unknown type: ") + \
                        header_column_data_types[index] + self.tr(", using the string type."))
                    QgsMessageLog.logMessage(self.tr("CSVT file has column that has unknown type: ") + \
                                             header_column_data_types[index] + self.tr(", using the string type."),
                                             "DigitransitGeocoder", Qgis.Warning)
                    fields.append(QgsField(header_column, QVariant.String))
                else:
                    fields.append(QgsField(header_column, QVariant.Double, len=length, prec=precision))
            else:
                fields.append(QgsField(header_column, QVariant.Double, len=length, prec=precision))

        elif col_data_type == 'date':
            fields.append(QgsField(header_column, QVariant.Date))
        elif col_data_type == 'time':
            fields.append(QgsField(header_column, QVariant.Time))
        elif col_data_type == 'datetime':
            fields.append(QgsField(header_column, QVariant.DateTime))
        elif col_data_type == 'wkt' or col_data_type == 'point(x/y)':
            fields.append(QgsField(header_column, QVariant.String))
        elif col_data_type == 'coordx' or col_data_type == 'coordy':
            fields.append(QgsField(header_column, QVariant.Double))
        elif col_data_type == 'point(x)' or col_data_type == 'point(y)':
            fields.append(QgsField(header_column, QVariant.Double))
        else:
            # self.iface.messageBar().pushMessage(
            #    self.tr("CSVT file problem"),
            #    self.tr("CSVT file has column that has unknown type: ") + \
            #    col_data_types[index] + self.tr(", using the string type."),
            #    QgsMessageBar.WARNING,
            #    10)
            self.feedback.pushInfo(
                self.tr("CSVT file has column that has unknown type: ") + \
                header_column_data_types[index] + self.tr(", using the string type."))
            QgsMessageLog.logMessage(self.tr("CSVT file has column that has unknown type: ") + \
                                     header_column_data_types[index] + self.tr(", using the string type."),
                                     "DigitransitGeocoder", Qgis.Warning)
            fields.append(QgsField(header_column, QVariant.String))

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
                'size': self.max_n_of_search_results
            }

            if self.use_source_OA or self.use_source_OSM or self.use_source_NLS:
                sources = ""
                if self.use_source_NLS:
                    sources = sources + "nlsfi,"
                if self.use_source_OA:
                    sources = sources + "oa,"
                if self.use_source_OSM:
                    sources = sources + "osm,"
                sources = sources.rstrip(',')
                search_parameters['sources'] = sources
            else:
                QgsMessageLog.logMessage(self.tr('No data sources selected. Please, select at least one data source.'),
                                         "DigitransitGeocoder", Qgis.Critical)
                self.feedback.reportError(
                    self.tr("No data sources selected. Please, select at least one data source."))
                raise DigitransitGeocoderPluginAlgorithmError()

            if self.use_location_type_address or self.use_location_type_venue or self.use_location_type_street:
                layers = ""
                if self.use_location_type_address:
                    layers = layers + "address,"
                if self.use_location_type_venue:
                    layers = layers + "venue,"
                if self.use_location_type_street:
                    layers = layers + "street,"
                layers = layers.rstrip(',')
                search_parameters['layers'] = layers
            else:
                QgsMessageLog.logMessage(
                    self.tr('No types of locations to search selected. Please, select at least one of the streets, venues and addresses.'),
                    "DigitransitGeocoder", Qgis.Critical)
                self.feedback.reportError(
                    self.tr("No types of locations to search selected. Please, select at least one of the streets, venues and addresses."))
                raise DigitransitGeocoderPluginAlgorithmError()

            query_string = urllib.parse.urlencode(search_parameters)

            search_URL = base_URL + query_string
            if self.bounds != None:
                search_URL += self.bounds

            QgsMessageLog.logMessage(search_URL, "DigitransitGeocoder", Qgis.Info)

            r = urllib.request.urlopen(search_URL)
            geocoding_result = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
            # QgsMessageLog.logMessage(str(geocoding_result), "DigitransitGeocoder", Qgis.Info)

            if self.feedback.isCanceled():
                return

            self.geocode_count += 1

            n_of_features = len(geocoding_result['features'])

            if n_of_features > 0:
                n_of_search_result_rows = \
                    self.max_n_of_search_result_rows \
                        if n_of_features >= self.max_n_of_search_result_rows \
                        else n_of_features

                for feature in geocoding_result['features'][:n_of_search_result_rows]:

                    qgs_feature = QgsFeature()
                    lon = feature['geometry']['coordinates'][0]
                    lat = feature['geometry']['coordinates'][1]
                    qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))

                    values = list(row)

                    # also add a few of the geocoding result feature properties if available
                    properties = feature['properties']
                    values.append(properties['id']) # digitransit_id
                    gid = ''
                    if 'gid' in properties:
                        gid = properties['gid']
                    values.append(gid)
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
                    source_id = ''
                    if 'source_id' in properties:
                        source_id = properties['source_id']
                    values.append(source_id)
                    name = ''
                    if 'name' in properties:
                        name = properties['name']
                    values.append(name)
                    localadmin = ''
                    if 'localadmin' in properties:
                        localadmin = properties['localadmin']
                    values.append(localadmin)
                    localadmin_gid = ''
                    if 'localadmin_gid' in properties:
                        localadmin_gid = properties['localadmin_gid']
                    values.append(localadmin_gid)
                    locality = ''
                    if 'locality' in properties:
                        locality = properties['locality']
                    values.append(locality)
                    locality_gid = ''
                    if 'locality_gid' in properties:
                        locality_gid = properties['locality_gid']
                    values.append(locality_gid)
                    postalcode = -1
                    if 'postalcode' in properties:
                        postalcode = properties['postalcode']
                    values.append(postalcode)
                    postalcode_gid = ''
                    if 'postalcode_gid' in properties:
                        postalcode_gid = properties['postalcode_gid']
                    values.append(postalcode_gid)
                    region = ''
                    if 'region' in properties:
                        region = properties['region']
                    values.append(region)
                    region_gid = ''
                    if 'region_gid' in properties:
                        region_gid = properties['region_gid']
                    values.append(region_gid)
                    country = ''
                    if 'country' in properties:
                        country = properties['country']
                    values.append(country)
                    country_gid = ''
                    if 'country_gid' in properties:
                        country_gid = properties['country_gid']
                    values.append(country_gid)
                    country_a = ''
                    if 'country_a' in properties:
                        country_a = properties['country_a']
                    values.append(country_a)
                    neighbourhood = ''
                    if 'neighbourhood' in properties:
                        neighbourhood = properties['neighbourhood']
                    values.append(neighbourhood)
                    neighbourhood_gid = ''
                    if 'neighbourhood_gid' in properties:
                        neighbourhood_gid = properties['neighbourhood_gid']
                    values.append(neighbourhood_gid)
                    label = ''
                    if 'label' in properties:
                        label = properties['label']
                    values.append(label)
                    values.append(search_URL)

                    qgs_feature.setAttributes(values)

                    # Add a feature in the sink
                    self.sink.addFeature(qgs_feature, QgsFeatureSink.FastInsert)

                    # QgsMessageLog.logMessage("Added a feature", "DigitransitGeocode    r", Qgis.Info)

            else:
                self.feedback.pushInfo(
                    self.tr("Geocode not succesful for the address: ") + address)
                QgsMessageLog.logMessage(self.tr("Geocode not succesful for the address: ") + address, "DigitransitGeocoder",
                                         Qgis.Warning)

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
        return QCoreApplication.translate('DigitransitGeocoderPluginAlgorithm', string)

    def createInstance(self):
        return DigitransitGeocoderPluginAlgorithm()
