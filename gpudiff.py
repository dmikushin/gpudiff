#!/usr/bin/env python3

import argparse
from device_query import parse_device_query
from bandwidth_test import parse_bandwidth_test
from dashtable import data2rst
from collections import OrderedDict
import matplotlib.pyplot as plt

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

def diff_device_query(gpu1, gpu2):
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

def plot_bandwidth(ax, data, title, legend1, legend2):
    transfer_sizes = list(data.keys())
    bandwidths1 = [float(bw[0]) for bw in data.values()]
    bandwidths2 = [float(bw[1]) for bw in data.values()]

    ax.plot(transfer_sizes, bandwidths1, label=legend1, marker='o')
    ax.plot(transfer_sizes, bandwidths2, label=legend2, marker='o')
    ax.set_xlabel('Transfer Size (Bytes)')
    ax.set_ylabel('Bandwidth (GB/s)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

    # Set sparse ticks (adjust the divisor as needed)
    tick_spacing = max(1, len(transfer_sizes) // 10)
    ax.set_xticks(transfer_sizes[::tick_spacing])
    ax.set_xticklabels(transfer_sizes[::tick_spacing], rotation=45)

def diff_bandwidth_test(gpu1, gpu2):
    h2d = merge(gpu1['h2d'], gpu2['h2d'])
    d2h = merge(gpu1['d2h'], gpu2['d2h'])
    d2d = merge(gpu1['d2d'], gpu2['d2d'])

    fig, axs = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle('GPU Memory Bandwidth Comparison')

    plot_bandwidth(axs[0][0], h2d, 'Host to Device Bandwidth', gpu1['device_name'], gpu2['device_name'])
    plot_bandwidth(axs[1][0], d2h, 'Device to Host Bandwidth', gpu1['device_name'], gpu2['device_name'])
    plot_bandwidth(axs[0][1], d2d, 'Device to Device Bandwidth', gpu1['device_name'], gpu2['device_name'])

    # Hide the unused subplot at position (1,1)
    axs[1][1].axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Compare two GPU logs.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subparser for device query
    device_query_parser = subparsers.add_parser('device-query', help='Compare device query logs')
    device_query_parser.add_argument('logfile1', help='Path to the first device query log file')
    device_query_parser.add_argument('logfile2', help='Path to the second device query log file')

    # Subparser for bandwidth test
    bandwidth_test_parser = subparsers.add_parser('bandwidth-test', help='Compare bandwidth test logs')
    bandwidth_test_parser.add_argument('logfile1', help='Path to the first bandwidth test log file')
    bandwidth_test_parser.add_argument('logfile2', help='Path to the second bandwidth test log file')

    args = parser.parse_args()

    # Open the log files and read the entire logs into strings
    with open(args.logfile1, 'r') as file:
        log1 = file.read()

    with open(args.logfile2, 'r') as file:
        log2 = file.read()

    if args.command == 'device-query':
        gpu1 = parse_device_query(log1)
        gpu2 = parse_device_query(log2)
        diff_device_query(gpu1, gpu2)
    elif args.command == 'bandwidth-test':
        gpu1 = parse_bandwidth_test(log1)
        gpu2 = parse_bandwidth_test(log2)
        diff_bandwidth_test(gpu1, gpu2)

if __name__ == "__main__":
    main()

