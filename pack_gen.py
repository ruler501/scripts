#!/usr/bin/env python3
"""Convert from Google Sheets csv storage for cube to CubeCobra csv."""
import argparse
import csv
import random
import sys
from collections import OrderedDict
from typing import Iterable


def read_file(filename: str) -> Iterable[OrderedDict]:
    """Iterate over the lines of the csv file as an OrderedDict."""
    with open(filename, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield row


def main(input_file: str, output_file: str, to_cube_cobra: bool = False, to_google_sheets: bool = False) -> int:
    """Convert the csv file specified by filename."""
    if to_cube_cobra:
        output = ["Name,CMC,Type,Color,Set,Collector Number,Status,Tags"]
        special_columns = ['Card Name', 'Colors', 'CMC', 'Rarity', 'Rating', 'Set',
                           'Main Theme', 'Secondary Theme', 'Tertiary Theme',
                           'Power', 'Toughness', "Collector's Number"]
        rarity_map = {'C': 'Common', 'U': 'Uncommon', 'R': 'Rare', 'L': 'Land'}
        cards = []
        for row in read_file(input_file):
            if len(row['Card Name']) == 0:
                continue
            name = row['Card Name']
            cmc = row['CMC']
            color = row['Colors']
            color = color.replace('/', '').replace('-', '')
            if color == "GW":
                color = "WG"
            elif color == "RW":
                color = "WR"
            elif color == "GU":
                color = "UG"
            card_set = row['Set']
            status = 'Not Owned'
            collectors_number = row["Collector's Number"]
            try:
                if int(row['Premium']):
                    status = 'Premium Owned'
            except ValueError:
                pass
            if status == "Not Owned":
                try:
                    if int(row['Have Copy']):
                        status = 'Owned'
                except ValueError:
                    pass
            rarity = rarity_map.get(row['Rarity'], 'No Rarity')
            tags = [rarity]
            rating = row['Rating']
            if len(rating) > 0:
                tags.append(f'rating-{rating}')
            for column, value in row.items():
                if column not in special_columns:
                    try:
                        if int(value):
                            tags.append(column)
                    except ValueError:
                        pass
            card = {
             "name": name,
             "rarity": rarity
            }
            cards.append(card)
            output.append(f'"{name}",{cmc},,{color},{card_set},{collectors_number},{status},"{", ".join(tags)}"')
            print(output[-1])
        commons = [card for card in cards if card["rarity"] == "Common"]
        uncommons = [card for card in cards if card["rarity"] == "Uncommon"]
        rares = [card for card in cards if card["rarity"] == "Rare"]
        lands = [card for card in cards if card["rarity"] == "Land"]
        random.shuffle(commons)
        random.shuffle(uncommons)
        random.shuffle(rares)
        random.shuffle(lands)
        with open(output_file+'-p1.dck', 'w') as out_file:
            pool = ['COMMONS:', ''] + sorted(commons[:60], key=lambda c: c['name']) + ['', 'UNCOMMONS:', ''] + sorted(uncommons[:24], key=lambda c: c['name']) + ['', 'RARES:', ''] + sorted(rares[:6], key=lambda c: c['name']) + ['', 'LANDS:', ''] + sorted(lands[:6], key=lambda c: c['name'])
            out_file.write('\n'.join(str(card) for card in pool))
        with open(output_file+'-p2.dck', 'w') as out_file:
            pool = ['COMMONS:', ''] + sorted(commons[60:120], key=lambda c: c['name']) + ['', 'UNCOMMONS:', ''] + sorted(uncommons[24:48], key=lambda c: c['name']) + ['', 'RARES:', ''] + sorted(rares[6:12], key=lambda c: c['name']) + ['', 'LANDS:', ''] + sorted(lands[6:12], key=lambda c: c['name'])
            out_file.write('\n'.join(str(card) for card in pool))
        with open(output_file+'-p3.dck', 'w') as out_file:
            pool = ['COMMONS:', ''] + sorted(commons[120:180], key=lambda c: c['name']) + ['', 'UNCOMMONS:', ''] + sorted(uncommons[48:72], key=lambda c: c['name']) + ['', 'RARES:', ''] + sorted(rares[12:18], key=lambda c: c['name']) + ['', 'LANDS:', ''] + sorted(lands[12:18], key=lambda c: c['name'])
            out_file.write('\n'.join(str(card) for card in pool))
        # with open(output_file, 'w') as out_file:
        #     out_file.write('\n'.join(output))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert between Google Sheets csv and Cube Cobra csv for cube.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--to-cube-cobra', action='store_true', help="Import to CubeCobra format for csv.")
    group.add_argument('--to-google-sheets', action='store_true', help="Export to Google Sheets format for csv.")
    parser.add_argument('--input-file', type=str, help="The file to import/export from.", required=True)
    parser.add_argument('--output-file', type=str, help="The file to import/export to.", required=True)
    sys.exit(main(**vars(parser.parse_args())))
