#!/usr/bin/env python3
import requests
import json
import re
import os
import time
import sys

BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
TERMS_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terms_map.json")
README_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")

HEADERS = {
    "User-Agent": "QuantumForge-KnowledgeBot/1.0 (research project; contact@quantumforge.dev)"
}

TITLES = [
    "Darth_Vader", "Luke_Skywalker", "Princess_Leia", "Han_Solo",
    "Obi-Wan_Kenobi", "Yoda", "Palpatine", "Chewbacca",
    "Lando_Calrissian", "Boba_Fett", "R2-D2", "C-3PO",
    "Darth_Maul", "Count_Dooku", "General_Grievous", "Qui-Gon_Jinn",
    "Mace_Windu", "Jabba_the_Hutt", "Ahsoka_Tano", "Kylo_Ren",
    "Rey_(Star_Wars)", "Finn_(Star_Wars)", "Tatooine", "Hoth",
    "Endor_(Star_Wars)", "Dagobah", "Naboo", "Coruscant",
    "Bespin", "Mustafar", "Geonosis", "Kamino_(Star_Wars)",
    "Yavin", "Alderaan", "Death_Star", "Lightsaber",
    "Jedi", "Sith", "The_Force", "Stormtrooper_(Star_Wars)",
    "TIE_fighter", "X-wing_fighter", "Millennium_Falcon", "Star_Destroyer",
    "Rebel_Alliance", "Galactic_Empire_(Star_Wars)", "Galactic_Republic",
    "Clone_trooper", "Mandalorian", "Darth_Sidious",
]

TERMS_MAP = {
    # Characters — longest multi-word first
    "Emperor Palpatine": "Overlord Malachar",
    "Darth Sidious": "Darth Vorrak",
    "Admiral Ackbar": "Admiral Kael",
    "Grand Moff Tarkin": "High Commander Draven",
    "Obi-Wan Kenobi": "Torin Mellis",
    "Princess Leia": "Lady Sera Aldrin",
    "Darth Vader": "Zarn Velkor",
    "Anakin Skywalker": "Kaelor Venn",
    "Luke Skywalker": "Dorin Venn",
    "Han Solo": "Jax Brennick",
    "Darth Maul": "Darth Kraven",
    "Count Dooku": "Lord Vexis",
    "General Grievous": "Warlord Krynn",
    "Qui-Gon Jinn": "Renn Solus",
    "Mace Windu": "Korr Vandar",
    "Jabba the Hutt": "Mogul Graxx",
    "Boba Fett": "Vex Kellan",
    "Lando Calrissian": "Daren Cole",
    "Ahsoka Tano": "Lyra",
    "Kylo Ren": "Varek",
    "Rey": "Nova",
    "Finn": "Cade",
    "Padmé Amidala": "Elara Vesper",
    "Shmi Skywalker": "Mira Venn",
    "Wedge Antilles": "Rik Dorn",
    "Poe Dameron": "Nix Jarrin",
    "Asajj Ventress": "Zara Nyx",
    "Jango Fett": "Varek Kellan",
    "R2-D2": "NX-7 astromech droid",
    "C-3PO": "VX-9 protocol droid",
    "BB-8": "KX-4 astromech",
    "Chewbacca": "Grokka",

    # Characters — single names (after multi-word)
    "Palpatine": "Malachar",
    "Yoda": "Zephyr",
    "Chewie": "Grokka",
    "Starkiller": "Vorlan",
    "Vader": "Velkor",
    "Kenobi": "Mellis",
    "Skywalker": "Venn",

    # Planets / Locations — longest first
    "Cloud City": "Cloud Station Nimbus",
    "Sanctuary Moon": "Sanctuary Moon",
    "Death Star": "Void Core",
    "Yavin 4": "Sanctuary Moon",
    "Yavin IV": "Sanctuary Moon",
    "Jakku": "Solara",
    "Scarif": "Helix Prime",
    "Jedha": "Vortis",
    "Kamino": "Okeanos",
    "Geonosis": "Kharon",
    "Mustafar": "Pyronis",
    "Bespin": "Cloud Station Nimbus",
    "Tatooine": "Kaelos",
    "Hoth": "Icyria",
    "Endor": "Veridia",
    "Dagobah": "Xylara",
    "Naboo": "Aetheris",
    "Coruscant": "Prime Nexus",
    "Alderaan": "Lyrandia",
    "Yavin": "Sanctuary Moon",

    # Technologies — longest first
    "Millennium Falcon": "Iron Phoenix",
    "TIE fighter": "Wrath-class interceptor",
    "X-wing fighter": "Starhawk fighter",
    "Star Destroyer": "Obliterator-class cruiser",
    "AT-AT Walker": "Titan Strider",
    "AT-AT": "Titan Strider",
    "AT-ST": "Scout Strider",
    "Speeder bike": "Hover cycle",
    "Pulse rifle": "Palse rifle",
    "lightsaber": "Plasma Blade",
    "Lightsaber": "Plasma Blade",
    "hyperdrive": "Warp Coil",
    "Hyperdrive": "Warp Coil",
    "Blaster": "Palse rifle",
    "blaster": "palse rifle",

    # Factions — longest first
    "Galactic Empire": "Stellar Dominion",
    "Galactic Republic": "Interstellar Coalition",
    "Rebel Alliance": "Free Worlds Federation",
    "First Order": "Iron Ascendancy",
    "Trade Federation": "Commerce Guild",
    "Jedi Council": "Aether Conclave",
    "Jedi Order": "Aether Guard Order",
    "Sith Order": "Void Cabal Order",
    "Jedi Knight": "Aether Warden",
    "Sith Lord": "Void Master",
    "Jedi Master": "Aether Sage",
    "Sith Apprentice": "Void Acolyte",
    "Clone Wars": "Replicant Wars",
    "Order 66": "Protocol Zero",
    "The Force": "Synth Flux",
    "Jedi": "Aether Guard",
    "Sith": "Void Cabal",

    # Factions — single
    "Resistance": "Liberation Front",
    "Separatists": "Dissident Alliance",
    "Separatist": "Dissident",
    "Rebels": "Federation forces",
    "Rebel": "Federation",
    "Imperial": "Dominion",
    "Empire": "Dominion",
    "Republic": "Coalition",

    # Stormtroopers / Clone troopers
    "Stormtrooper": "Iron Legionnaire",
    "stormtrooper": "Iron Legionnaire",
    "Clone trooper": "Replicant soldier",
    "clone trooper": "Replicant soldier",
    "Stormtroopers": "Iron Legionnaires",
    "stormtroopers": "Iron Legionnaires",
    "Clone troopers": "Replicant soldiers",
    "clone troopers": "Replicant soldiers",
    "Mandalorian": "Iron Warden",
    "mandalorian": "Iron Warden",

    # Species — longest first
    "Tusken Raider": "Sand Nomad",
    "Tusken Raiders": "Sand Nomads",
    "Sand Nomads": "Sand Nomads",
    "Scrap Dwellers": "Scrap Dwellers",
    "Kaminoan": "Okeani",
    "Geonosian": "Khari",
    "Wookiee": "Hurog",
    "Wookiees": "Hurogs",
    "Ewok": "Veridi",
    "Ewoks": "Veridi",
    "Hutt": "Graxxi",
    "Hutts": "Graxxi",
    "Twi'lek": "Lethari",
    "Togruta": "Zelari",
    "Gungan": "Aethari",
    "Gungans": "Aethari",
    "Jawa": "Scrap Dwellers",
    "Jawas": "Scrap Dwellers",

    # The Force concepts
    "dark side of the Force": "shadow path of Synth Flux",
    "dark side": "shadow path",
    "light side of the Force": "radiant path of Synth Flux",
    "light side": "radiant path",
    "the Force": "Synth Flux",
    "Force-sensitive": "Flux-sensitive",
    "Force user": "Flux wielder",
    "Force powers": "Flux abilities",

    # Events / Media — longest first
    "The Phantom Menace": "The Shadow Rising",
    "Attack of the Clones": "Siege of the Replicants",
    "Revenge of the Sith": "Fall of the Aether Guard",
    "A New Hope": "Dawn of Freedom",
    "The Empire Strikes Back": "The Dominion Retaliates",
    "Return of the Jedi": "Return of the Aether Wardens",
    "The Force Awakens": "The Flux Awakens",
    "The Last Jedi": "The Last Aether Warden",
    "The Rise of Skywalker": "Rise of the Venn Legacy",
    "Rogue One": "Operation Void Core",
    "Battle of Yavin": "Battle of Sanctuary Moon",
    "Battle of Hoth": "Battle of Icyria",
    "Battle of Endor": "Battle of Veridia",

    # Additional concept terms
    "Star Wars": "Stellar Chronicles",
    "star wars": "Stellar Chronicles",
    "Galaxy": "Vortex Reach",
    "galaxy": "vortex reach",
    "Droid": "Automaton",
    "droid": "automaton",
    "Death Star plans": "Void Core schematics",
    "Super Star Destroyer": "Annihilator-class dreadnought",
    "X-wing": "Starhawk",
    "X-Wing": "Starhawk",
    "TIE fighter": "Wrath-class interceptor",
    "TIE": "Wrath",
    "Star Destroyers": "Obliterator-class cruisers",
    "DS-1": "VC-1",
    "DS-2": "VC-2",
}


def build_sorted_terms():
    """Return list of (pattern, replacement) sorted by pattern length descending."""
    items = list(TERMS_MAP.items())
    items.sort(key=lambda x: len(x[0]), reverse=True)
    return items


def replace_terms(text, sorted_terms):
    for term, replacement in sorted_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        text = re.sub(pattern, replacement, text)
    return text


def fetch_page(title):
    url = BASE_URL + title
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("extract", "")
    except Exception as e:
        print(f"  [ERROR] Failed to fetch '{title}': {e}", file=sys.stderr)
        return None


def sanitize_filename(title):
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', title)
    return safe + ".md"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sorted_terms = build_sorted_terms()
    print(f"Loaded {len(TERMS_MAP)} term replacements.")
    print(f"Sorted by length — checking longest-first priority is correct.\n")

    documents = []

    for idx, title in enumerate(TITLES, 1):
        print(f"[{idx}/{len(TITLES)}] Fetching: {title}")
        raw_text = fetch_page(title)

        if raw_text is None:
            print(f"  -> SKIPPED (fetch failed)\n")
            continue

        print(f"  -> Got {len(raw_text)} chars of raw text.")

        transformed = replace_terms(raw_text, sorted_terms)

        filename = sanitize_filename(title)
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(transformed)

        documents.append({"title": title, "file": filename, "chars": len(transformed)})
        print(f"  -> Saved to {filename} ({len(transformed)} chars after replacement)\n")

        time.sleep(0.3)

    with open(TERMS_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(TERMS_MAP, f, indent=2, ensure_ascii=False)
    print(f"Saved terms map ({len(TERMS_MAP)} entries) to {TERMS_MAP_PATH}")

    readme = """# The Stellar Chronicles — Knowledge Base

This is a fictional universe of **Stellar Chronicles**, a reimagined space-opera setting
originally derived from well-known cultural material and transformed through comprehensive
terminology replacement.

## The Universe

The **Vortex Reach** is governed by two opposing philosophies of **Synth Flux** — an
all-encompassing energy field connecting all living beings:

- **Radiant Path** — pursued by the **Aether Guard**, an ancient order of peacekeepers
  who wield Plasma Blades and channel Synth Flux for knowledge and defense.
- **Shadow Path** — embraced by the **Void Cabal**, masters of domination who twist
  Synth Flux to fuel their hunger for power.

## Major Factions

| Faction | Leader | Role |
|---|---|---|
| **Aether Guard** | Sage Zephyr / Aether Conclave | Guardians of peace in the Vortex Reach |
| **Void Cabal** | Overlord Malachar / Darth Vorrak | Seekers of absolute power |
| **Stellar Dominion** | Overlord Malachar | Authoritarian regime ruling the Vortex Reach |
| **Interstellar Coalition** | Galactic Senate | Democratic governing body (pre-Dominion) |
| **Free Worlds Federation** | Lady Sera Aldrin / Admiral Kael | Freedom fighters opposing the Dominion |
| **Iron Ascendancy** | Varek | Dominion remnant seeking restoration |
| **Liberation Front** | Nova, Cade, Nix Jarrin | Resistance against the Iron Ascendancy |

## Key Heroes

- **Dorin Venn** (originally Luke Venn, son of Kaelor) — Aether Warden, destroyer of the first Void Core
- **Kaelor Venn** — former Aether Warden turned Darth Vorrak, later redeemed
- **Zarn Velkor** — Kaelor's Void Master persona
- **Lady Sera Aldrin** — leader of the Free Worlds Federation
- **Jax Brennick** — smuggler and Federation general
- **Torin Mellis** — sage who trained both Kaelor and Dorin

## Key Planets / Locations

- **Prime Nexus** — city-planet, political center
- **Kaelos** — desert world, home of the Venn lineage
- **Aetheris** — lush world, birthplace of Lady Sera
- **Icyria** — frozen wasteland, site of a major battle
- **Veridia** — forest moon, home of the Veridi species
- **Xylara** — swamp world where Zephyr lived in exile
- **Pyronis** — volcanic world, site of Kaelor's fall
- **Okeanos** — water world, origin of the Replicant Army

## Technology

- **Plasma Blade** — energy sword wielded by Aether Wardens and Void Masters
- **Void Core** — moon-sized battle station capable of planetary destruction
- **Starhawk Fighter** — primary starfighter of the Federation
- **Wrath-class Interceptor** — Dominion starfighter
- **Iron Phoenix** — modified freighter captained by Jax Brennick
- **Obliterator-class Cruiser** — massive Dominion capital ship

## Major Conflicts

- **The Shadow Rising** — emergence of Darth Vorrak
- **Siege of the Replicants** — start of the Replicant Wars
- **Fall of the Aether Guard** — Protocol Zero nearly wipes out the Aether Guard
- **Dawn of Freedom** — the first Void Core destroyed at the Battle of Sanctuary Moon
- **The Dominion Retaliates** — Dominion strikes back, truth about Kaelor revealed
- **Return of the Aether Wardens** — second Void Core destroyed, Malachar falls
- **The Flux Awakens** — Iron Ascendancy rises
- **The Last Aether Warden** — Dorin Venn's final sacrifice
- **Rise of the Venn Legacy** — final defeat of the Void Cabal

---

*Generated for QuantumForge Software RAG bot research project. All names are fictional.*
"""
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"Saved README.md to {README_PATH}")

    print(f"\n{'=' * 60}")
    print(f"BUILD COMPLETE")
    print(f"  Total titles attempted : {len(TITLES)}")
    print(f"  Successfully saved     : {len(documents)}")
    print(f"  Failed                 : {len(TITLES) - len(documents)}")
    print(f"  Term replacements      : {len(TERMS_MAP)}")
    print(f"  Output directory       : {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()