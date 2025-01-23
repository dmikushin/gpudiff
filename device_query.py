#!/usr/bin/env python3

# Parse "deviceQuery" CUDA sample output

import argparse
import json
import re
from collections import OrderedDict

def extract_device_info(log):
    device_pattern = r'\s*Device 0: "(.+)"'
    info_pattern = r'\s*(.+?)\s*[:\s]\s+(.+)'
    smx_pattern = r'\s*\((\d+)\) Multiprocessors, \((\d+)\) CUDA Cores/MP:\s*(\d+) CUDA Cores'

    lines = log.splitlines()

    info = OrderedDict()

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
                    num_smx = str(int(match.group(1)))
                    num_cores_per_smx = str(int(match.group(2)))
                    num_cores = str(int(match.group(3)))
                    info['Total number of CUDA cores'] = num_cores
                    info['Total number of CUDA multiprocessors'] = num_smx
                    info['Total number of CUDA cores per multiprocessor'] = num_cores_per_smx
                    continue
                if name in ['Run time limit on kernels', 'CUDA Driver Version / Runtime Version', 'Device PCI Domain ID / Bus ID / location ID']:
                    continue
                info[name] = value
            else:
                break
                
    return info

def parse_device_query(log):
    return extract_device_info(log)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse "deviceQuery" CUDA sample output.')
    parser.add_argument('filename', type=str, help='The path to the log file')
    args = parser.parse_args()

    with open(args.filename, 'r') as file:
        log = file.read()

    result = parse_device_query(log)

    json_string = json.dumps(result, indent=4)
    print(json_string)

    with open(f'{args.filename}.json', 'w') as file:
        file.write(json_string)

