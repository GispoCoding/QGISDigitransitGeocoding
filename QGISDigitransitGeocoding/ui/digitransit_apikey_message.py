from qgis.PyQt import QtWidgets

from ..qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS = load_ui("digitransit_geocoder_apikey_message.ui")


class KeyMissingDlg(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""

        # noinspection PyArgumentList
        super(KeyMissingDlg, self).__init__(parent)
        self.setupUi(self)
        t2 = self.tr("ERROR: No DIGITRANSIT_API_KEY variable found.")
        t3 = self.tr(
            "You may get a subscription to the Digitransit geocoding API from the "
        )
        t4 = self.tr("Digitransit API Portal")
        t5 = self.tr(
            "In order to use this plugin, you must create a global variable"
            + " DIGITRANSIT_API_KEY in QGIS and set the your API key"
            + " (also known as subscription key)"
            + " as the value."
        )
        t6 = self.tr(
            "A QGIS global variable can be set in"
            + " Settings &gt; Options &gt; Variables tab."
        )
        t7 = self.tr(
            "Please note that the global variable is QGIS"
            + " profile specific and may be viewed in plain text"
            + " in the settings window."
        )
        self.label.setText(
            f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
            "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html><head><meta name="qrichtext" content="1" /><style type="text/css">
        p, li {{ white-space: pre-wrap; }}
        </style></head><body style="font-family:'MS Shell Dlg 2';
            font-size:8pt; font-weight:400; font-style:normal; margin: 0;">
        <p style="margin: 12px 0 0 0; -qt-block-indent:0; text-indent:0px;">{t2}</p>
        <p style="margin: 12px 0 0 0; -qt-block-indent:0; text-indent:0px;">{t3}
            <a href="https://portal-api.digitransit.fi/"
            style="text-decoration: none; color:#0000ff;">{t4}</a>.</p>
        <p style="margin: 12px 0 0 0; -qt-block-indent:0; text-indent:0px;">{t5}</p>
        <p style="margin: 12px 0 0 0; -qt-block-indent:0; text-indent:0px;">{t6}</p>
        <p style="margin: 12px 0 0 0; -qt-block-indent:0; text-indent:0px;">{t7}</p>
        </body></html>"""
        )
