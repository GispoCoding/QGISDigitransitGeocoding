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
from PyQt5.QtCore import pyqtSignal, QMetaObject, pyqtSlot
#from PyQt5.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsMessageLog
from PyQt5 import  QtNetwork
from PyQt5.QtCore import QUrl

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'digitransit_geocoder_dockwidget_base.ui'))


class DigitransitGeocoderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
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

        QgsMessageLog.logMessage(self.lineEditAddress.text(),
                                 'Search term',
                                 Qgis.Info)

    def geocode(self, search_text):
        baseURL = "http://api.digitransit.fi/geocoding/v1/search"