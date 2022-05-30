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

import os  # noqa F401

from .qgis_plugin_tools.infrastructure.debugging import setup_debugpy  # noqa F401
from .qgis_plugin_tools.infrastructure.debugging import setup_ptvsd  # noqa F401
from .qgis_plugin_tools.infrastructure.debugging import setup_pydevd  # noqa F401

debugger = os.environ.get("QGIS_PLUGIN_USE_DEBUGGER", "").lower()
if debugger in {"debugpy", "ptvsd", "pydevd"}:
    locals()["setup_" + debugger]()


def classFactory(self):  # noqa N802
    from .plugin import Plugin

    return Plugin()
