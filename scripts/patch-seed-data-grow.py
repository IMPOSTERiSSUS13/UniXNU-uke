#!/usr/bin/env python3
import sys
from pathlib import Path

target_file = Path(sys.argv[1])
text = target_file.read_text()

old_block = """        try:
            listing = plistlib.loads(subprocess.check_output(['diskutil', 'apfs', 'list', '-plist']))
            container = None
            for entry in listing['Containers']:
                if any(s['DeviceIdentifier'] == store for s in entry.get('PhysicalStores', [])):
                    container = entry['ContainerReference']
            if not container:
                sys.exit('No APFS container found on the attached seed')
            run('diskutil', 'apfs', 'resizeContainer', container, '0')"""

new_block = """        try:
            import time
            container = None
            print('hdiutil attach result:', repr(attached))
            print('Detected store identifier:', store)
            for attempt in range(20):
                time.sleep(1)
                try:
                    listing = plistlib.loads(subprocess.check_output(['diskutil', 'apfs', 'list', '-plist']))
                    for entry in listing.get('Containers', []):
                        for s in entry.get('PhysicalStores', []):
                            dev = s.get('DeviceIdentifier', '')
                            if dev == store or dev.startswith(store):
                                container = entry.get('ContainerReference')
                                print(f'Found container {container} for store {dev} at attempt {attempt+1}')
                                break
                        if container:
                            break
                    if container:
                        break
                except Exception as e:
                    print(f'Attempt {attempt+1} listing error: {e}')
            if not container:
                print('--- diskutil list ---')
                subprocess.run(['diskutil', 'list'])
                print('--- diskutil apfs list ---')
                subprocess.run(['diskutil', 'apfs', 'list'])
                sys.exit('No APFS container found on the attached seed')
            print(f'Resizing container {container} to fill disk...')
            run('diskutil', 'apfs', 'resizeContainer', container, '0')
            print('Container resize successful!')"""

if old_block not in text:
    print('WARNING: old_block not found in', target_file)
    sys.exit(1)

target_file.write_text(text.replace(old_block, new_block))
print('Successfully patched', target_file)
