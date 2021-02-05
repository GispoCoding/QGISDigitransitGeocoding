# QGISDigitransitGeocoding

This QGIS3 plugin is developed for searching and geocoding Finnish places and addresses.
It is based on <a href="https://digitransit.fi/">digitransit.fi</a> geocoding API that utilizes data from
the <a href="https://www.maanmittauslaitos.fi/en">National Land Survey of Finland</a>,
<a href="https://dvv.fi/en/individuals">Popularion Register Center of Finland</a> and
<a href="https://www.openstreetmap.org/">OpenStreetMap</a>.

The plugin is still in beta-development. Please report issues preferably to Issues or to tuki@gispo.fi.

Developed by **Gispo Ltd**.

## Installation instructions

1. Download the latest release zip from GitHub releases (above) either via Clone or Download ZIP.
2. Launch QGIS and navigate to the plugins menu by selecting Plugins - Manage and Install Plugins from the top menu.
3. Select the Install from ZIP tab, browse to the zip file you just downloaded, and click Install Plugin!

## Käyttö

Käyttöön on kaksi mahdollisuutta:
1. Lisäosan ajo yksittäisten osoitteiden geokoodamiseksi onnistuu Lisäosat-valikosta:
   Lisäosat | Digitransit.fi-geokoodaus | Geokoodaa suomalainen osoite. Käyttöliittymän oikeaan osaan aukeaa paneeli,
   jonka "Osoite"-kenttään voi kirjoittaa osoitteen tai osoitteen osan. Hae-painikkeella haetaan ja listataan
   osoitteita ja paikkoja. Riippuen asetuksista, hakutulokset lisätään myös suoraan karttatasoksi.
   Paneelin alaosan setuksista voi myös säätää muita hakuehtoja.
2. Jos sinulla on CSV-tiedosto, joka sisältää paikkoja/osoitteita, niin voit geokoodata ne käyttämällä
   lisäosan prosessointi-ominaisuutta, joka löytyy QGIS:n prosessointityökalujen alta.

## Aineistolähteet

Aineistolähteinä ovat
<a href="http://www.maanmittauslaitos.fi/kartat-ja-paikkatieto/asiantuntevalle-kayttajalle/maastotiedot-ja-niiden-hankinta" target="_blank">Maanmittauslaitoksen Maastotietokanta</a>,
<a href="https://www.avoindata.fi/data/fi/dataset/rakennusten-osoitetiedot-koko-suomi" target="_blank">Väestörekisterikeskus</a>
ja <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>.
Maanmittauslaitoksen maastotieokanta ja Väestörekisterikeskuksen aineisto on lisensoitu
<a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">Creative Commons Nimeä 4.0 Kansainvälinen -lisenssillä</a>.
OpenStreetMap-aineisto on lisensoitu <a href="https://opendatacommons.org/licenses/odbl/" target="_blank">ODbL-lisenssillä</a>.
