"""Install the bundled release APK and verify native onboarding renders."""
import glob
import pathlib
import subprocess
import time
import xml.etree.ElementTree as ET

out = pathlib.Path('artifacts/android')
out.mkdir(parents=True, exist_ok=True)

def adb(*args):
    return subprocess.check_output(['adb', *args])

adb('install', '-r', glob.glob('android/app/build/outputs/apk/release/*.apk')[0])
adb('shell', 'am', 'start', '-n', 'com.x3ra4.smak/.MainActivity')
found = False
for _ in range(30):
    time.sleep(2)
    adb('shell', 'uiautomator', 'dump', '/sdcard/smak.xml')
    xml = adb('shell', 'cat', '/sdcard/smak.xml').decode('utf-8')
    (out / 'onboarding.xml').write_text(xml, encoding='utf-8')
    if 'Почати готувати' in xml:
        found = True
        break
(out / 'onboarding.png').write_bytes(adb('exec-out', 'screencap', '-p'))
(out / 'logcat.txt').write_bytes(adb('logcat', '-d'))
assert found, 'Native onboarding did not render; inspect logcat and screenshot'
root = ET.fromstring(xml)
button = next(node for node in root.iter('node') if 'Почати готувати' in (node.get('text', '') + node.get('content-desc', '')))
import re
x1, y1, x2, y2 = map(int, re.findall(r'\d+', button.attrib['bounds']))
adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
time.sleep(10)
adb('shell', 'uiautomator', 'dump', '/sdcard/smak.xml')
xml = adb('shell', 'cat', '/sdcard/smak.xml').decode('utf-8')
(out / 'discover.xml').write_text(xml, encoding='utf-8')
(out / 'discover.png').write_bytes(adb('exec-out', 'screencap', '-p'))
assert 'Що приготуємо' in xml, 'Discover screen did not render'
print('Native APK: onboarding and discover verified on Android emulator')
