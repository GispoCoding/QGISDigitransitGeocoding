# QGISDigitransitGeocoding

This QGIS plugin is developed for searching and geocoding Finnish places and addresses.
It is based on <a href="https://digitransit.fi/">digitransit.fi</a> geocoding API that utilizes data from
the <a href="https://www.maanmittauslaitos.fi/en">National Land Survey of Finland</a>,
<a href="https://dvv.fi/en/individuals">Popularion Register Center of Finland</a> and
<a href="https://www.openstreetmap.org/">OpenStreetMap</a>.

Please report issues preferably to Issues or to info@gispo.fi. The plugin is still is not actively developed, but if you want to support the development or request a feature, do not hesitate to contact us.

Developed by **Gispo Ltd**.

## Installation instructions

1. Via QGIS plugin repository: Launch QGIS and navigate to the plugins menu by selecting Plugins > Manage and Install Plugins from the top menu. Go to All tab and search for Digitransit.fi Geocoder and click Install Plugin!

2. From ZIP-file: Go to green Code button and choose Download ZIP option. Lauch QGIS and navigate to plugins menu (as in 1), but this time, go to Install from ZIP tab, set the correct path to the ZIP file you just downloaded and click Install Plugin!

## Usage

As of 03.04.2023 the Digitransit API requires an subscription key. This subscription key (API key) can be acquired from
https://portal-api.digitransit.fi/. In order to use the plugin, you must set a global variable in QGIS using the following steps:

1. In QGIS, press Settings > Options.
2. Switch to the Variables tab.
3. Add a new variable by clicking the plus (+) sign.
4. Name the variable "DIGITRANSIT_API_KEY" (without the quotation marks).
5. Copy the API key to your clipboard.
6. Paste your API key as the value of the newly created variable.

There are two alternative ways to use the plugin: to geocode an individual Finnish address / place or to geocode a
list of addresses / places (given as a CSV file).

In the first case, the required steps are:
1. Navigate to the plugins menu by selecting Plugins - Digitransit.fi Geocoder - Geocode a Finnish address or
   click the Digitransit.fi Geocoder plugin icon.
2. The plugin panel opens to the right edge of the user interface. Write the address (or a part of the address)
   you are interested in to the Address field and hit Search button.
3. The way the results get presented depends on the applied settings. The obtained results may either get printed
   out as a list into a window locating below the Search field, or get added to the map canvas as a new temporary
   scratch layer.
4. The rest of the panel offers a wide range of tuning possibilities. In there, you can modify the settings
   related to Search parameters and Search results. The opportunity for resetting current settings and
   restoring default ones can be found at the bottom of the panel.

In the second case, the desired functionality of the plugin can be found by selecting Processing tab from the QGIS top
menu bar and navigating to Toolbox - Digitransit.fi geocoding plugin - Geocode - Geocode addresses in a CSV file.
By double clicking it, a pop-up window opens. In Geocode Addresses in a CSV File window:
1. Determine the source file by browsing to the correct CSV file.
2. Give the column name(s) of the csv file containing address information.
3. Determine the data sources to be used in the search, number of locations to search and the number of result rows
   per CSV row.
4. Activate the check boxes according to your willingness to search for streets, venues and addresses.
5. Give a name for the output layer (if not given, a temporary scratch layer gets created) and click Run! You can
   follow the progress of the geocoding process from the processing bar.

Note that in QGIS, a temporary scratch file can easily be exported and made permanent.

## Data sources

The data utilized in this plugin is from
<a href="http://www.maanmittauslaitos.fi/kartat-ja-paikkatieto/asiantuntevalle-kayttajalle/maastotiedot-ja-niiden-hankinta" target="_blank">Maanmittauslaitoksen Maastotietokanta</a>,
<a href="https://dvv.fi/digi-ja-vaestotietovirasto" target="_blank">Digi- ja väestövirasto (DVV)</a>
and <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>.
The terrain database of the National Land Survey (NLS) and the Population Register Centre (via OpenAddresses) data are
licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0 license</a>. The OpenStreetMap data is licensed
under <a href="https://opendatacommons.org/licenses/odbl/">ODbL license</a>.
