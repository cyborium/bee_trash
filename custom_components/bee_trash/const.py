# SPDX-License-Identifier: GPL-3.0-or-later
# Modified from aha_trash by soundstorm (https://github.com/soundstorm/aha_trash)
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

DOMAIN = "bee_trash"
MANUFACTURER = "BEE Emden"

CONF_BEZIRK = "bezirk"

ABFALLARTEN = ["Restabfall", "Papier", "Gelber Sack"]

BEZIRKE = {
    "Larrelt": "larrelt",
    "Constantia": "constantia",
    "Port Arthur / Transvaal": "port-arthur-transvaal",
    "Hafen": "hafen",
    "Barenburg / Harsweg": "barenburg-harsweg",
    "Twixlum / Wybelsum / Logumer Vorwerk / Knock": "twixlum-wybelsum-logumer-vorwerk-knock",
    "Kulturviertel - südlich Früchteburger Weg / Gewerbegebiet 2. Polderweg": "kulturviertel-sudlich-fruchteburger-weg-gewerbegebiet-2-polderweg",
    "Conrebbersweg": "conrebbersweg",
    "Kulturviertel - nördlich Früchteburger Weg": "kulturviertel-nordlich-fruchteburger-weg",
    "Wolthusen": "wolthusen",
    "AOK-Viertel / Großfaldern": "aok-viertel-grossfaldern",
    "Kleinfaldern / Herrentor / Neuer Delft": "kleinfaldern-herrentor",
    "Friesland / Borssum / Hilmarsum": "friesland-borssum-hilmarsum",
    "Amtsgerichtsviertel und Ringstraße / Am Tonnenhof": "amtsgerichtsviertel-und-ringstrasse-am-tonnenhof",
    "Altstadt": "altstadt",
    "Jarssum / Widdelswehr": "jarssum-widdelswehr",
    "Petkum Uphusen / Tholenswehr / Marienwehr": "petkum-uphusen-tholenswehr-marienwehr",
}

ICS_URL_TEMPLATE = "https://www.bee-emden.de/abfall/entsorgungssystem/abfuhrkalender/ics/{slug}/abfuhrkalender.ics"
