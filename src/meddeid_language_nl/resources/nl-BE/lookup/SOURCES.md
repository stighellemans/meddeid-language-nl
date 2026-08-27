# Lookup data sources

The lookup files in this directory combine resources historically distributed
with DEDUCE with Belgian public-data additions. Values have been selected,
cleaned, normalised, deduplicated, and in some cases supplemented with spelling
or abbreviation variants.

These portable text resources are maintained independently of any recognizer.
Their historical DEDUCE lineage remains part of the provenance: when
redistributing or using them, retain this notice and cite Belgian DEDUCE. For
the underlying method, cite:

> Menger, V.J., Scheepers, F., van Wijk, L.M., Spruit, M. (2017). DEDUCE: A
> pattern matching method for automatic de-identification of Dutch medical
> text. *Telematics and Informatics*.

## Belgian additions

- **Names:** Statbel first-name and family-name tables, 2025. Source: Statbel
  (Direction générale Statistique – Statistics Belgium), distributed under
  CC BY 4.0. <https://statbel.fgov.be/en/open-data>
- **Streets, municipalities, and postal localities:** Statbel's 2024 address
  file with statistical sectors, distributed under CC BY 4.0.
  <https://statbel.fgov.be/en/open-data/address-file-statistical-sector-0>
- **Municipality supplements:** Dutch and French Wikipedia municipality pages.
  Wikipedia contributors; reused under CC BY-SA 4.0.
  <https://creativecommons.org/licenses/by-sa/4.0/>
- **Hospitals:** public hospital and emergency-care directories published by
  the Belgian Federal Public Service Health, Food Chain Safety and Environment.
  <https://www.health.belgium.be/>
- **Healthcare institutions:** public data from the Vlaamse Sociale Kaart.
  Required attribution: “Bevat data die ter beschikking worden gesteld door de
  Vlaamse overheid (www.desocialekaart.be).”
  <https://www.desocialekaart.be/handleiding/hergebruik-van-gegevens>
- **Walloon healthcare supplements:** public directories published by AVIQ.
  <https://www.aviq.be/>

These packaged text files are the runtime form used by the MedDeID `nl-BE`
language profile. Belgian DEDUCE may consume data from the same source lineage,
but it is not a package dependency of this language profile or the MedDeID
suite.
