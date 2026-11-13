# food-picture-01 — Steaming Bowl of Ramen

A make.fun entry: a program that draws one appetizing food picture.

**Concept:** a steaming bowl of ramen in a lacquered red bowl — golden
broth with wavy noodles, soft-boiled egg, chashu, narutomaki, scallions,
pickled ginger and nori, chopsticks lifting a tangle of noodles, steam
curling up, on a wooden table against a warm glowing background.

**How it works:** `main.py` (Python 3.13, standard library only) draws
every pixel from fixed constants with a hand-written PNG encoder
(IHDR / IDAT / IEND, filter 0, zlib level 9). No network, no randomness,
no time, no external files — two runs write byte-identical PNG bytes.

**Output:** `/output/entry.png`, PNG, 1024 x 1024 px, 21,859 bytes.

**Run it:** `python3 main.py`
