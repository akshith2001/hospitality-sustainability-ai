# Data sources

## Building Data Genome Project 2 (BDG2)

- **Dataset:** Building Data Genome Project 2, version 1.0
- **Creators:** Clayton Miller, Anjukan Kathirgamanathan, Bianca Picchetti,
  Pandarasamy Arjunan, June Young Park, Zoltan Nagy, Paul Raftery, Brodie W.
  Hobson, Zixiao Shi and Forrest Meggers
- **DOI:** https://doi.org/10.5281/zenodo.3887306
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Downloaded:** 2026-08-16
- **Official ZIP MD5:** `44393dc4cf61e84dec105e955368c890`
- **Verified downloaded MD5:** `44393dc4cf61e84dec105e955368c890`

The source contains hourly meter, weather and metadata records for non-residential
buildings. This repository's importer selects electricity-metered buildings classified
as `Food sales and service`, plus buildings whose subindustry is `Hotel`. It aggregates
hourly electricity to daily kWh when at least 20 hourly readings are available and joins
daily mean air temperature by site and date.

The source's building identifiers are already pseudonymous. The derived subset does not
contain employee, customer or event-client names.

### Important interpretation boundary

The selected buildings are hospitality-related according to BDG2 metadata, but the data
do not include customer counts, opening hours, equipment counts or verified intervention
outcomes. Results from this subset must not be described as proof that the full operational
hospitality model saves energy.
