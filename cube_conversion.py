#!/usr/bin/env python3
"""Convert from Google Sheets csv storage for cube to CubeCobra csv."""
import argparse
import csv
import sys
from collections import OrderedDict
from typing import Dict, Iterable, List, Set, Union

RARITY_MAP = {'C': 'Common', 'U': 'Uncommon', 'R': 'Rare', 'L': 'Land'}
REVERSE_RARITY_MAP = {value: key for key, value in RARITY_MAP.items()}
COLOR_MAP = {"GW": "WG", "RW": "WR", "GU": "UG"}
SPECIAL_COLUMNS = ['Card Name', 'Rarity', 'Colors', 'CMC', 'Rating', 'Set',
                   'Collector Number', 'Have Copy', 'Premium', 'Foil',
                   'Image URL', 'Power', 'Toughness', 'Type Line']
RATING_PREFIX = "Rating"
POWER_PREFIX = "Power"
TOUGHNESS_PREFIX = "Toughness"
COLORS_PREFIX = "Colors"
CMC_PREFIX = "CMC"


def read_file(filename: str) -> Iterable[OrderedDict]:
    """Iterate over the lines of the csv file as an OrderedDict."""
    with open(filename, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for entry in reader:
            yield entry


def convert_to_cube_cobra(entries: Iterable[OrderedDict]) -> Iterable[str]:
    """Provide a stream of lines for a cube_cobra csv corresponding to the same entries."""
    yield "Name,CMC,Type,Color,Set,Collector Number,Status,Finish,Maybeboard,Image URL,Tags"
    for entry in entries:
        if len(entry['Card Name']) == 0:
            continue
        name = entry['Card Name']
        cmc = entry['CMC']
        color = entry['Colors']
        color = color.replace('/', '').replace('-', '')
        if color in COLOR_MAP:
            color = COLOR_MAP[color]
        card_set = entry['Set']
        collector_number = entry['Collector Number']
        type_line = entry.get('Type Line', '')
        imgUrl = entry.get('Image URL', '')
        if entry.get('Premium', None) == '1':
            status = 'Premium Owned'
        elif entry.get('Have Copy', None) == '1':
            status = 'Owned'
        else:
            status = 'Not Owned'
        if entry.get('Foil', None) == '1':
            finish = "Foil"
        else:
            finish = "Non-foil"
        rarity = entry.get('Rarity', None)
        if rarity.endswith('-C'):
            maybe = 'true'
            rarity = rarity[:-2]
        else:
            maybe = 'false'
        rarity = RARITY_MAP.get(rarity, 'No Rarity')
        tags = [rarity, f'{COLORS_PREFIX}-{entry["Colors"]}', f'{CMC_PREFIX}-{cmc}']
        if len(entry["Power"]) > 0:
            tags.append(f'{POWER_PREFIX}-{entry["Power"]}')
        if len(entry["Toughness"]) > 0:
            tags.append(f'{TOUGHNESS_PREFIX}-{entry["Toughness"]}')
        if len(entry["Rating"]) > 0:
            tags.append(f'{RATING_PREFIX}-{entry["Rating"]}')
        for column, value in entry.items():
            if column not in SPECIAL_COLUMNS:
                try:
                    if value == '1':
                        tags.append(column)
                except ValueError:
                    pass
        tags_str = ",  ".join(tag.strip() for tag in tags)
        line = f'"{name}",{cmc},{type_line},{color},{card_set},{collector_number},{status},{finish},{maybe},{imgUrl},"{tags_str}"'  # noqa: E501
        print(line)
        yield line


def convert_to_sheets(entries: Iterable[OrderedDict]) -> Iterable[str]:
    """Provide a stream of lines for a cube_cobra csv corresponding to the same entries."""
    all_tags: Set[str] = set()
    converted_data: List[Dict[str, Union[str, int]]] = []
    for entry in entries:
        data: Dict[str, Union[str, int]] = dict()
        data["Card Name"] = f'"{entry["Name"]}"'
        data["Colors"] = entry["Color"]
        data["Set"] = f'"{entry["Set"].upper()}"'
        data["Collector Number"] = entry["Collector Number"]
        data['Type Line'] = f'"{entry["Type"]}"'
        data['Image URL'] = f'"{entry["Image URL"]}"'
        if entry['Finish'] == 'Foil':
            data['Foil'] = 1
        else:
            data['Foil'] = 0
        if entry['Status'] == 'Premium Owned':
            data['Have Copy'] = 1
            data['Premium'] = 1
        else:
            if entry['Status'] == 'Owned':
                data['Have Copy'] = 1
            else:
                data['Have Copy'] = 0
            data['Premium'] = 0
        tags = entry["Tags"].split(",")
        for tag in tags:
            tag = tag.strip()
            if tag.startswith(RATING_PREFIX):
                data["Rating"] = tag[len(RATING_PREFIX) + 1:]
            elif tag in REVERSE_RARITY_MAP:
                rarity = REVERSE_RARITY_MAP[tag]
                if entry['Maybeboard'] == 'true':
                    rarity += '-C'
                data['Rarity'] = rarity
            elif tag.startswith(POWER_PREFIX):
                data["Power"] = tag[len(POWER_PREFIX) + 1:]
            elif tag.startswith(TOUGHNESS_PREFIX):
                data["Toughness"] = tag[len(TOUGHNESS_PREFIX) + 1:]
            elif tag.startswith(COLORS_PREFIX):
                data["Colors"] = tag[len(COLORS_PREFIX) + 1:]
            elif tag.startswith(CMC_PREFIX):
                data['CMC'] = tag[len(CMC_PREFIX) + 1:]
            else:
                if tag not in all_tags:
                    all_tags.add(tag)
                data[tag] = 1
        converted_data.append(data)
    columns = SPECIAL_COLUMNS + sorted(all_tags)
    columns_line = ",".join(f'"{column}"' for column in columns)
    print(columns_line)
    yield columns_line
    for converted_entry in converted_data:
        data = {key: "" for key in SPECIAL_COLUMNS}
        data.update({key: 0 for key in all_tags})
        data.update(converted_entry)
        line = ",".join(str(data[column]) for column in columns)
        print(line)
        yield line


def main(input_file: str, output_file: str, to_cube_cobra: bool = False, to_google_sheets: bool = False) -> int:
    """Convert the csv file specified by filename."""
    entries = read_file(input_file)
    if to_cube_cobra:
        output = convert_to_cube_cobra(entries)
    elif to_google_sheets:
        output = convert_to_sheets(entries)
    else:
        raise Exception("Must specify cube_cobra or google_sheets")
    with open(output_file, 'w') as out_file:
        out_file.write('\n'.join(output))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert between Google Sheets csv and Cube Cobra csv for cube.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--to-cube-cobra', action='store_true', help="Import to CubeCobra format for csv.")
    group.add_argument('--to-google-sheets', action='store_true', help="Export to Google Sheets format for csv.")
    parser.add_argument('--input-file', type=str, help="The file to import/export from.", required=True)
    parser.add_argument('--output-file', type=str, help="The file to import/export to.", required=True)
    sys.exit(main(**vars(parser.parse_args())))
