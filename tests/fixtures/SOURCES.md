# afyna fixture sources

afyna's fixture tree contains nine FLAC recordings and three PNG images.

## Audio fixtures

| File                                | Upstream recording                                                                                                              | Author / credit                                                            | License | SHA-256                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------ |
| `audio/22sq.flac`                   | <https://commons.wikimedia.org/wiki/File:22SQ_song.flac>                                                                        | CT-17 Capt. Yoichi Kurono; 1980-02-18                                      | CC0 1.0 | `a586cb7dec1d7c093f7379e703d5e03fc851f0b42913a59cffea4ffff67bf8c7` |
| `audio/black-cat-begging.flac`      | <https://commons.wikimedia.org/wiki/File:Black_cat_sound_begging_the_foods.flac>                                                | Wikimedia Commons user 매일 누군가가 도둑맞을 때마다; own work; 2026-09-28 | CC0 1.0 | `b66ea66b161e665eb721da95111162504d6c41343c7ca81dd4bb35f6ff68334a` |
| `audio/blackbird.flac`              | <https://commons.wikimedia.org/wiki/File:Common_blackbird_singing_denoised.flac>                                                | tinga; 2013-05-07                                                          | CC0 1.0 | `8ab7f670c60c314fbe8ecf1afb5301211f43a671e159c8ffb7a460635fa799e1` |
| `audio/flamenco-road.flac`          | <https://commons.wikimedia.org/wiki/File:Flamenco_road.flac>                                                                    | Michael Laucke; 2001-09-03                                                 | CC0 1.0 | `23389861477c304f98c4889bf3a0103569edeb9d23da45e67574625e97362790` |
| `audio/flanger-distorted-bass.flac` | <https://commons.wikimedia.org/wiki/File:Flanger_with_distorted_electric_bass.flac>                                             | Sentree; own work; 2025-08-23                                              | CC0 1.0 | `90f077fc19af2145fd1664d76ffcd11b2ace360e6bb579a2e44c6b429085cd90` |
| `audio/hans-im-schnokeloch.flac`    | <https://commons.wikimedia.org/wiki/File:D%E2%80%99r_Hans_im_Schnokeloch_%E2%80%93_Simple_Arrangement.flac>                     | Nachtbold; 2025-02-23                                                      | CC0 1.0 | `1bbc9c26cccc348dea50c9168bf8dc2cf12c63f3080238ff1ef5909755d1f7a0` |
| `audio/ietf-cellar-subset-47.flac`  | <https://github.com/ietf-wg-cellar/flac-test-files/blob/main/subset/47%20-%20only%20STREAMINFO.flac>                            | IETF CELLAR FLAC test files, Martijn van Beurden                           | CC0 1.0 | `bbe9e3f9de202ead28adeaa9ff14521effe42fa5b9699793b3f4813cbf6ce24b` |
| `audio/minuet.flac`                 | <https://commons.wikimedia.org/wiki/File:Minuet_in_G_major,_BWV_Anh._114_(played_by_PLATO_GSW).flac>                            | Morn; 2022-11-20                                                           | CC0 1.0 | `99f1f66ae40f2713ddd7afcb685a2c7b57f10c487ae66912574afa4bd9991202` |
| `audio/unfa-braam.flac`             | <https://commons.wikimedia.org/wiki/File:647712_unfa_braam.flac> (original: <https://freesound.org/people/unfa/sounds/647712/>) | Unfa (Tobiasz "unfa" Karoń); Freesound 647712; 2022-08-22                  | CC0 1.0 | `17bdf6ce4d1be1c6b84e0e3f51a8b5adac891c3910e97a921039a4a61ef17e31` |

### Vorbis-comment baseline

Every FLAC has exactly these five Vorbis-comment fields, once each:

`ALBUM`, `ALBUMARTIST`, `ARTIST`, `TITLE`, `TRACKNUMBER`.

| File                                | `ALBUM`             | `ALBUMARTIST`        | `ARTIST`             | `TITLE`                           | `TRACKNUMBER` |
| ----------------------------------- | ------------------- | -------------------- | -------------------- | --------------------------------- | ------------- |
| `audio/22sq.flac`                   | Fixture Album Two   | Fixture Artist Two   | Fixture Artist Two   | 22SQ                              | 2             |
| `audio/black-cat-begging.flac`      | Fixture Album Three | Fixture Artist Three | Fixture Artist Three | Black cat sound begging the foods | 1             |
| `audio/blackbird.flac`              | Fixture Album One   | Fixture Artist One   | Fixture Artist One   | Blackbird                         | 2             |
| `audio/flamenco-road.flac`          | Fixture Album One   | Fixture Artist One   | Fixture Artist One   | Flamenco Road                     | 1             |
| `audio/flanger-distorted-bass.flac` | Fixture Album Four  | Fixture Artist Four  | Fixture Artist Four  | Fixture Title Four                | 1             |
| `audio/hans-im-schnokeloch.flac`    | Fixture Album Two   | Fixture Artist Two   | Fixture Artist Two   | D'r Hans im Schnokeloch           | 1             |
| `audio/ietf-cellar-subset-47.flac`  | Fixture Album Six   | Fixture Artist Six   | Fixture Artist Six   | Fixture Title Six                 | 1             |
| `audio/minuet.flac`                 | Fixture Album One   | Fixture Artist One   | Fixture Artist One   | Minuet in G Major                 | 3             |
| `audio/unfa-braam.flac`             | Fixture Album Five  | Fixture Artist Five  | Fixture Artist Five  | Fixture Title Five                | 1             |

### Embedded picture

`audio/hans-im-schnokeloch.flac` carries one FLAC picture block:

- Type 4 (Cover (back)), PNG, 968x968, 24-bit
- Data length 562743 bytes
- Payload SHA-256: `57f315a313c02f184e24253e4370998fba1b372d59b67c6f8e699ddff4639373`

## Image fixtures

| File                       | Source                                                                       | License / status              | SHA-256                                                            |
| -------------------------- | ---------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| `images/fall-hazard.png`   | Original composition using original photographs                              | Composition dedicated CC0 1.0 | `10e0aa01b80027191dcc319c955a9762915a3ba9af23da91efc4e10769a4fa73` |
| `images/forest-road.png`   | Original composition using original photographs                              | Composition dedicated CC0 1.0 | `ebdce98f880ec8d70a09485ba06427f286d6436269d6de75f2a29d50eebbd176` |
| `images/inevitability.png` | Original composite using the four public-domain photographs documented below | Composition dedicated CC0 1.0 | `6d55b782faad373db0782ee50bce92316a4425228dc3ff8a544a1a301f94403e` |

### `inevitability.png` source photographs

The four photographs are U.S. federal government works in the public domain; the
composite is separately dedicated to CC0 1.0.

| Source                                                                                                     | Author / credit                                               | Date       | Photo ID    | Status                     |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ---------- | ----------- | -------------------------- |
| <https://commons.wikimedia.org/wiki/File:Operation_Doorstep_-_Destruction_of_house_n%C2%B01_-_Frame_1.jpg> | National Nuclear Security Administration / Nevada Site Office | 1953-03-17 | UK-53-001-1 | U.S. federal public domain |
| <https://commons.wikimedia.org/wiki/File:NNSA-NSO-76.jpg>                                                  | National Nuclear Security Administration / Nevada Site Office | 1953-03-17 | UK-53-010   | U.S. federal public domain |
| <https://commons.wikimedia.org/wiki/File:Operation_Doorstep_-_Destruction_of_house_n%C2%B01_-_Frame_7.jpg> | National Nuclear Security Administration / Nevada Site Office | 1953-03-17 | UK-53-004-7 | U.S. federal public domain |
| <https://commons.wikimedia.org/wiki/File:OperationDoorstep2-ManLivingroom.jpg>                             | United States Department of Energy                            | 1953       | S-22-5      | U.S. federal public domain |
