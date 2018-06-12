# QGISDigitransitGeocoding

QGIS 3 plugin that is meant for searching and geocoding Finnish places and addresses. It utilizes the <a href="https://digitransit.fi/">digitransit.fi</a> geocoding API that utilizes data from the <a href="http://www.maanmittauslaitos.fi/en">National Land Survey of Finland</a>, <a href="http://vrk.fi/en/frontpage">Popularion Register Center of Finland</a> and <a href="https://www.openstreetmap.org/">OpenStreetMap</a>.

## Asennusohjeet

1. Lisäosa tulee asentaa erillisestä sijainnista ja sen takia QGIS:ssä valitse ensiksi Lisäosat-valikosta: Hallitse ja asenna lisäosia... | Asetukset.
2. Asetuksissa kytke käyttöön "Näytä myös kokeelliset laajennusosat" ja edelleen napauta "Lisää..."-painiketta.
3. Avautuvassa dialogissa anna haluamasi nimi esim. "Gispon QGIS-lisäosat" ja anna URL-kentän arvoksi https://s3.eu-central-1.amazonaws.com/gispoqgisplugins/gispo_qgis_plugins.xml ja napauta OK.
4. Valitse edelleen avoinna olevassa Laajennusosat-ikkunassa Kaikki-välilehti. Hae lisäosa nimellä "Digitransit.fi Geocoder" ja napauta "Asenna lisäosa"-painiketta.
5. Asennuksen jälkeen voit sulkea Lisäosat-ikkunan.

## Käyttö

Käyttöön on kaksi mahdollisuutta:
1. Lisäosan ajo yksittäisten osoitteiden geokoodamiseksi onnistuu Lisäosat-valikosta: Lisäosat | Digitransit.fi-geokoodaus | Geokoodaa suomalainen osoite. Käyttöliittymän oikeaan osaan aukeaa paneeli, jonka "Osoite"-kenttään voi kirjoittaa osoitteen tai osoitteen osan. Hae-painikkeella haetaan ja listataan osoitteita ja paikkoja. Riippuen asetuksista, hakutulokset lisätään myös suoraan karttatasoksi. Paneelin alaosan setuksista voi myös säätää muita hakuehtoja.
2. Jos sinulla on CSV-tiedosto, joka sisältää paikkoja/osoitteita, niin voit geokoodata ne käyttämällä lisäosan prosessointi-ominaisuutta, joka löytyy QGIS:n prosessointityökalujen alta.

## Aineistolähteet

Aineistolähteinä ovat <a href="http://www.maanmittauslaitos.fi/kartat-ja-paikkatieto/asiantuntevalle-kayttajalle/maastotiedot-ja-niiden-hankinta" target="_blank">Maanmittauslaitoksen Maastotietokanta</a>, <a href="https://www.avoindata.fi/data/fi/dataset/rakennusten-osoitetiedot-koko-suomi" target="_blank">Väestörekisterikeskus</a> ja <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>. Maanmittauslaitoksen maastotieokanta ja Väestörekisterikeskuksen aineisto on lisensoitu <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">Creative Commons Nimeä 4.0 Kansainvälinen -lisenssillä</a>. OpenStreetMap-aineisto on lisensoitu <a href="https://opendatacommons.org/licenses/odbl/" target="_blank">ODbL-lisenssillä</a>.
