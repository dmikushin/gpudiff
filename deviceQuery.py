#!/usr/bin/env python3

# Parse "deviceQuery" CUDA sample output

import argparse
import json
import re

def extract_device_info(log):
    device_pattern = r'\s*Device 0: "(.+)"'
    info_pattern = r'\s*(.+?)\s*[:\s]\s+(.+)'
    smx_pattern = r'\s*\((\d+)\) Multiprocessors, \((\d+)\) CUDA Cores/MP:\s*(\d+) CUDA Cores'

    lines = log.splitlines()

    info = {}

    device_pattern_found = False
    for line in lines:
        match = re.search(device_pattern, line)
        if match:
            info['Device Name'] = match.group(1)
            device_pattern_found = True
        elif device_pattern_found:
            match = re.search(info_pattern, line)
            if match:
                name = match.group(1)
                value = match.group(2)
                match = re.search(smx_pattern, line)
                if match:
                    num_smx = match.group(1)
                    num_cores_per_smx = match.group(2)
                    num_cores = 	match.group(3)
                    info['Total number of CUDA codes'] = num_cores
                    info['Total number of CUDA multiprocessors'] = num_smx
                    info['Total number of CUDA cores per multiprocessor'] = num_cores_per_smx
                    continue
                if name == 'CUDA Driver Version / Runtime Version':
                    # The driver/runtime version is a machine-specific property
                    # unrelated to the GPU itself, so we should skip it.
                    continue
                if name == 'Device PCI Domain ID / Bus ID / location ID':
                    # The hardware address is a machine-specific property
                    # unrelated to the GPU itself, so we should skip it.
                    continue
                info[name] = value
            else:
                break
                
    return info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse "deviceQuery" CUDA sample output.')
    parser.add_argument('filename', type=str, help='The path to the log file')
    args = parser.parse_args()

    # Open the log file and read the entire log into a string
    with open(args.filename, 'r') as file:
        log = file.read()

    result = extract_device_info(log)

    # Convert dictionary to JSON string
    json_string = json.dumps(result, indent=4)
    print(json_string)

    # Write JSON string to a file
    with open(f'{args.filename}.json', 'w') as file:
        file.write(json_string)
