#!/usr/bin/env python3

# Parse "bandwidthTest --mode=shmoo" CUDA sample output

import argparse
import json
import re

def extract_device_name(log):
    device_pattern = r"\s+Device\s+0:\s*(.*)"

    lines = log.splitlines()

    for line in lines:
        match = re.search(device_pattern, line)
        if match:
            device_name = match.group(1)
            return device_name

def extract_bandwidth(log, pattern1, pattern2, pattern3):
    pattern_data = r"\s*(\d+)\s*([\d.]+)"

    lines = log.splitlines()

    data = {}

    pattern1_found = False
    pattern2_found = False
    pattern3_found = False
    for line in lines:
        match = re.search(pattern1, line)
        if match:
            pattern1_found = True
        elif pattern1_found:
            match = re.search(pattern2, line)
            if match:
                pattern2_found = True
            elif pattern2_found:
                match = re.search(pattern3, line)
                if match:
                    pattern3_found = True
                elif pattern3_found:
                    match = re.search(pattern_data, line)
                    if match:
                        size = match.group(1)
                        bandwidth = match.group(2)
                        data[size] = bandwidth
                    else:
                        break
                else:
                    return {}
            else:
                return {}

    return data

def extract_h2d_bandwidth(log):
    pattern1 = r"\s*Host to Device Bandwidth, 1 Device\(s\)"
    pattern2 = r"\s*PINNED Memory Transfers"
    pattern3 = r"\s*Transfer Size \(Bytes\)\tBandwidth\(GB/s\)"
    return extract_bandwidth(log, pattern1, pattern2, pattern3)

def extract_d2h_bandwidth(log):
    pattern1 = r"\s*Device to Host Bandwidth, 1 Device\(s\)"
    pattern2 = r"\s*PINNED Memory Transfers"
    pattern3 = r"\s*Transfer Size \(Bytes\)\tBandwidth\(GB/s\)"
    return extract_bandwidth(log, pattern1, pattern2, pattern3)

def extract_d2d_bandwidth(log):
    pattern1 = r"\s*Device to Device Bandwidth, 1 Device\(s\)"
    pattern2 = r"\s*PINNED Memory Transfers"
    pattern3 = r"\s*Transfer Size \(Bytes\)\tBandwidth\(GB/s\)"
    return extract_bandwidth(log, pattern1, pattern2, pattern3)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse "bandwidthTest --mode=shmoo" CUDA sample output.')
    parser.add_argument('filename', type=str, help='The path to the log file')
    args = parser.parse_args()

    # Open the log file and read the entire log into a string
    with open(args.filename, 'r') as file:
        log = file.read()

    result = {}

    result['device_name'] = extract_device_name(log)

    result['h2d'] = extract_h2d_bandwidth(log)
    result['d2h'] = extract_d2h_bandwidth(log)
    result['d2d'] = extract_d2d_bandwidth(log)

    # Convert dictionary to JSON string
    json_string = json.dumps(result, indent=4)
    print(json_string)

    # Write JSON string to a file
    with open(f'{args.filename}.json', 'w') as file:
        file.write(json_string)
