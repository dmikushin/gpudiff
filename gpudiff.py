#!/usr/bin/env python3

import argparse
from device_query import parse_device_query
from bandwidth_test import parse_bandwidth_test
from dashtable import data2rst
from collections import OrderedDict

def merge(dict1: OrderedDict, dict2: OrderedDict):
    """Merge values of two OrderedDicts into tuples with the same key, using 'N/A' for missing keys."""
    merged = OrderedDict()
    keys1 = list(dict1.keys())
    keys2 = list(dict2.keys())
    all_keys = []

    # Interleave keys from both dicts
    i, j = 0, 0
    while i < len(keys1) or j < len(keys2):
        if i < len(keys1) and keys1[i] not in all_keys:
            all_keys.append(keys1[i])
        if j < len(keys2) and keys2[j] not in all_keys:
            all_keys.append(keys2[j])
        i += 1
        j += 1

    # Merge dicts based on interleaved keys
    for key in all_keys:
        merged[key] = (dict1.get(key, 'N/A'), dict2.get(key, 'N/A'))

    return merged

def find_neighbors(lines, i, j):
    """Find neighboring horizontal and vertical symbols for a given position, ignoring non-frame symbols."""
    # Define valid frame symbols
    frame_symbols = {'-', '=', '|', '+'}

    # Helper function to get a character or a space if it's not a frame symbol
    def get_frame_symbol(line, index):
        if 0 <= index < len(line) and line[index] in frame_symbols:
            return line[index]
        return ' '

    above = get_frame_symbol(lines[i - 1], j) if i > 0 else ' '
    below = get_frame_symbol(lines[i + 1], j) if i < len(lines) - 1 else ' '
    left = get_frame_symbol(lines[i], j - 1) if j > 0 else ' '
    right = get_frame_symbol(lines[i], j + 1) if j < len(lines[i]) - 1 else ' '

    return f'{left}{right}{lines[i][j]}{above}{below}'

def convert_to_ext_ascii_frames(table_str):
    """Convert the basic ncurses-style table frames into extended ASCII symbols."""
    
    # Define the translation of basic ASCII to extended ASCII frame symbols
    translate = {
    	# Left, right, above, below
        "---  ": '─',
        "===  ": '═',
        "  |||": '│',
        "  |++": '│',
        " -+ |": '┌',
        "- + |": '┐',
        " -+| ": '└',
        "- +| ": '┘',
        "--+||": '┼',
        " -+||": '├',
        "- +||": '┤',
        "--+ |": '┬',
        "--+| ": '┴',
        " =+||": '╞',
        "= +||": '╡',
        "+--  ": '─',
        "-+-  ": '─',
        "+==  ": '═',
        "=+=  ": '═',
        "==+||": '╪',
        "==+| ": '╧',
    }

    # Split the table into lines
    lines = table_str.splitlines()
    lines_out = []

    # Process each line to replace symbols
    for i, line in enumerate(lines):
        line_out = list(line)
        for j, char in enumerate(line):
            neighbors = find_neighbors(lines, i, j)
            if neighbors in translate:
                line_out[j] = translate[neighbors]
        lines_out.append(''.join(line_out))

    return '\n'.join(lines_out)

def gpudiff(gpu1, gpu2):
    # Extract device names or use 'N/A' if not available
    device_name1 = gpu1.get('Device Name', 'N/A')
    device_name2 = gpu2.get('Device Name', 'N/A')
    
    # Merge the dictionaries
    diff = merge(gpu1, gpu2)
    
    # Remove 'Device Name' from the diff
    diff.pop('Device Name', None)
    
    # Create a table with spans, if value is the same
    table = [
        ["Property", device_name1, device_name2]
    ]
    spans = []
    
    def mask(line):
        return line.replace('+', chr(255)).replace('-', chr(254)).replace('=', chr(253)).replace('|', chr(252))

    def unmask(line):
        return line.replace(chr(255), '+').replace(chr(254), '-').replace(chr(253), '=').replace(chr(252), '|')        
    
    for i, (key, (value1, value2)) in enumerate(diff.items()):
        key = mask(key)
        value1 = mask(value1)
        value2 = mask(value2)
        if value1 == value2:
            table.append([key, value1, ""])
            spans.append([[i + 1, 1], [i + 1, 2]])
        else:
            table.append([key, value1, value2])

    output = data2rst(table, spans=spans, use_headers=True)
    
    # TODO Read the table and replace +,-,=,| with extended ASCII symbols
    output = convert_to_ext_ascii_frames(output)
    
    print(unmask(output))
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two GPU device query logs.")
    parser.add_argument("logfile1", help="Path to the first device query log file")
    parser.add_argument("logfile2", help="Path to the second device query log file")
    
    args = parser.parse_args()
    
    # Open the log file and read the entire log into a string
    with open(args.logfile1, 'r') as file:
        log1 = file.read()

    # Open the log file and read the entire log into a string
    with open(args.logfile2, 'r') as file:
        log2 = file.read()

    # Parse the device query logs
    gpu1 = parse_device_query(log1)
    gpu2 = parse_device_query(log2)

    # Compare and display the differences
    gpudiff(gpu1, gpu2)

