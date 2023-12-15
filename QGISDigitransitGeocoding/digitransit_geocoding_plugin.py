# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISDigitransitGeocoding
                                 A QGIS plugin
 The plugin is meant for geocoding Finnish addresses
                              -------------------
        begin                : 2018-02-20
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Gispo, Ltd.
        email                : erno@gispo.fi
 ***************************************************************************/

"""
import os.path
from typing import Callable, List, Optional

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, Qt, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget
from qgis.utils import iface

from .core.digitransit_geocoder_processing_plugin_provider import (
    DigitransitProcessingPluginProvider,
)
from .qgis_plugin_tools.tools.custom_logging import setup_logger, teardown_logger
from .qgis_plugin_tools.tools.i18n import setup_translation, tr
from .qgis_plugin_tools.tools.resources import plugin_name, resources_path

# Import the code for the dialog
from .ui.digitransit_geocoder_dockwidget import DigitransitGeocoderDockWidget


class Plugin:
    """QGIS Plugin Implementation."""

    name = plugin_name()

    def __init__(self) -> None:
        """Constructor.
        :param iface: An interface instance that will be passed to this class
        which provides the hook by which you can manipulate the QGIS
        application at run time.
        :type iface: QgsInterface
        """
        setup_logger(Plugin.name)
        self.dockwidget = DigitransitGeocoderDockWidget(iface)
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale, file_path = setup_translation(
            "QGISDigitransitGeocoding_{}.qm", resources_path("/i18n")
        )
        if file_path:
            self.translator = QTranslator()
            self.translator.load(file_path)
            # noinspection PyCallByClass
            QCoreApplication.installTranslator(self.translator)
        else:
            pass

        # Declare instance attributes
        self.actions: List[QAction] = []
        self.menu = Plugin.name
        self.toolbar = iface.addToolBar("QGISDigitransitGeocoding")
        self.toolbar.setObjectName(tr("Digitransit.fi geocoding"))

        self.pluginIsActive = False

        self.processing_provider = DigitransitProcessingPluginProvider()

    def add_action(
        self,
        icon_path: str,
        text: str,
        callback: Callable,
        enabled_flag: bool = True,
        add_to_menu: bool = True,
        add_to_toolbar: bool = True,
        status_tip: Optional[str] = None,
        whats_this: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> QAction:
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.

        :param text: Text that should be shown in menu items for this action.

        :param callback: Function to be called when the action is triggered.

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.

        :param parent: Parent widget for the new action. Defaults None.

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            iface.addToolBarIcon(action)

        if add_to_menu:
            iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self) -> None:  # noqa N802
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.add_action(
            resources_path("icons/icon.png"),
            text=tr("Geocode a Finnish address"),
            callback=self.run,
            parent=iface.mainWindow(),
        )

        QgsApplication.processingRegistry().addProvider(self.processing_provider)

    def onClosePlugin(self) -> None:  # noqa N802
        """Cleanup necessary items here when plugin dockwidget is closed"""
        # Disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        self.pluginIsActive = False

    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            iface.removePluginMenu(Plugin.name, action)
            iface.removeToolBarIcon(action)
        teardown_logger(Plugin.name)

        # Remove the toolbar
        del self.toolbar

        QgsApplication.processingRegistry().removeProvider(self.processing_provider)

    def run(self) -> None:
        """Run method that performs all the real work aka loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            # Connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # Show the dockwidget
            iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.show()
