#!/usr/bin/env python3
import sys
from pathlib import Path

target_file = Path(sys.argv[1])
text = target_file.read_text()

old_block = """        attached = plistlib.loads(subprocess.check_output(
            ['hdiutil', 'attach', '-imagekey', 'diskimage-class=CRawDiskImage', '-nobrowse', '-owners', 'off',
             '-mountpoint', str(mount), '-plist', str(raw)]))
        device = attached['system-entities'][0]['dev-entry']
        try:
            if not (mount / 'mobile').is_dir():
                sys.exit('The Data seed has no /mobile; wrong base image?')
            merge_pref(mount, 'com.apple.migration', {
                'LastSystemVersion': BUILD,
                'DMUserDataDisposition': {'SyntheticDidUpgrade': False, 'buildVersion': BUILD}})
            merge_pref(mount, 'com.apple.springboard', {
                'BKNoWatchdogs': True,
                'FBLaunchWatchdogExceptions': {'com.apple.purplebuddy': 100.0},
                'MCForceShowCloudConfigurationUI': False,
                **({'SBDisableAutoDim': True, 'SBDontDimOrLockOnAC': True, 'SBDisableIdleSleep': True} if no_auto_dim else {})})
            merge_pref(mount, 'com.apple.purplebuddy', {
                'SetupDone': True, 'SetupFinishedAllSteps': True, 'SetupVersion': 11, 'daemonizeNeedsToRun': False})
            merge_pref(mount, 'com.apple.purplebuddy.notbackedup', {
                k: False for k in ('ShouldRunDiagnosticsMiniBuddy', 'ShouldRunHSA2MiniBuddy', 'ShouldRunKeychainSyncMiniBuddy',
                                   'ShouldRunMesaMiniBuddy', 'ShouldRunPaymentMiniBuddy', 'ShouldRunStandardMiniBuddy',
                                   'SilentICDPUpgrade')})
            merge_pref(mount, 'com.apple.managedconfiguration.notbackedup', {
                'LockdownActivationIndicatesCloudConfigurationAvailable': False})
            for sub in ('Bundle', 'Data/System', 'Shared/SystemGroup', 'Temp'):
                d = mount / 'containers' / sub
                if not d.is_dir():
                    d.mkdir(parents=True)
                    os.chmod(d, 0o755)
                    print('mkdir', d.relative_to(mount))
        finally:
            subprocess.run(['hdiutil', 'detach', device], check=True)"""

new_block = """        attached = plistlib.loads(subprocess.check_output(
            ['hdiutil', 'attach', '-imagekey', 'diskimage-class=CRawDiskImage', '-nobrowse', '-owners', 'off',
             '-mountpoint', str(mount), '-plist', str(raw)]))
        print('hdiutil attach entities:', repr(attached.get('system-entities', [])))
        device = attached['system-entities'][0]['dev-entry']
        actual_mount = mount
        try:
            import time
            if not (actual_mount / 'mobile').is_dir():
                for ent in attached.get('system-entities', []):
                    mp = ent.get('mount-point')
                    if mp and (Path(mp) / 'mobile').is_dir():
                        actual_mount = Path(mp)
                        print(f'Found mount at {actual_mount}')
                        break
            if not (actual_mount / 'mobile').is_dir():
                for ent in attached.get('system-entities', []):
                    dev = ent.get('dev-entry')
                    if dev:
                        subprocess.run(['diskutil', 'mount', '-mountPoint', str(mount), dev], check=False)
                        if (mount / 'mobile').is_dir():
                            actual_mount = mount
                            print(f'Mounted {dev} at {mount}')
                            break
            if not (actual_mount / 'mobile').is_dir():
                print('--- diskutil list ---')
                subprocess.run(['diskutil', 'list'])
                sys.exit(f'The Data seed has no /mobile at {actual_mount}; wrong base image?')
            merge_pref(actual_mount, 'com.apple.migration', {
                'LastSystemVersion': BUILD,
                'DMUserDataDisposition': {'SyntheticDidUpgrade': False, 'buildVersion': BUILD}})
            merge_pref(actual_mount, 'com.apple.springboard', {
                'BKNoWatchdogs': True,
                'FBLaunchWatchdogExceptions': {'com.apple.purplebuddy': 100.0},
                'MCForceShowCloudConfigurationUI': False,
                **({'SBDisableAutoDim': True, 'SBDontDimOrLockOnAC': True, 'SBDisableIdleSleep': True} if no_auto_dim else {})})
            merge_pref(actual_mount, 'com.apple.purplebuddy', {
                'SetupDone': True, 'SetupFinishedAllSteps': True, 'SetupVersion': 11, 'daemonizeNeedsToRun': False})
            merge_pref(actual_mount, 'com.apple.purplebuddy.notbackedup', {
                k: False for k in ('ShouldRunDiagnosticsMiniBuddy', 'ShouldRunHSA2MiniBuddy', 'ShouldRunKeychainSyncMiniBuddy',
                                   'ShouldRunMesaMiniBuddy', 'ShouldRunPaymentMiniBuddy', 'ShouldRunStandardMiniBuddy',
                                   'SilentICDPUpgrade')})
            merge_pref(actual_mount, 'com.apple.managedconfiguration.notbackedup', {
                'LockdownActivationIndicatesCloudConfigurationAvailable': False})
            for sub in ('Bundle', 'Data/System', 'Shared/SystemGroup', 'Temp'):
                d = actual_mount / 'containers' / sub
                if not d.is_dir():
                    d.mkdir(parents=True)
                    os.chmod(d, 0o755)
                    print('mkdir', d.relative_to(actual_mount))
        finally:
            subprocess.run(['hdiutil', 'detach', device, '-force'], check=False)
            for ent in attached.get('system-entities', []):
                dev = ent.get('dev-entry')
                if dev and dev != device:
                    subprocess.run(['hdiutil', 'detach', dev, '-force'], check=False)"""

if old_block not in text:
    print('WARNING: old_block not found in', target_file)
    sys.exit(1)

target_file.write_text(text.replace(old_block, new_block))
print('Successfully patched', target_file)
