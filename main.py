# Reads the data of the festival and prints its name.
# Run it from this folder: uv run main.py
#
# The three lines below open the file and turn its JSON text into Python
# dicts and lists. How they work is explained in step 05; for now, use them.

import json

with open("data/festival.json", encoding="utf-8") as file:
    festival = json.load(file)

print(festival["name"])
print(festival["first_day"], "-", festival["last_day"])
print(len(festival["venues"]), "venues", end=", ")
print(len(festival["artists"]), "artists", end=", ")
print(len(festival["performances"]), "performances")
