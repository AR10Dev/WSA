import sys

import requests
from xml.dom import minidom
import html
import warnings
import re
from pathlib import Path

warnings.filterwarnings("ignore")

arch = sys.argv[1]

release_name_map = {"retail": "Retail", "RP": "Release Preview",
                    "WIS": "Insider Slow", "WIF": "Insider Fast"}
release_type = sys.argv[2] if sys.argv[2] != "" else "Retail"
release_name = release_name_map[release_type]

released_version = sys.argv[3]

cat_id = '858014f3-3934-4abe-8078-4aa193e74ca8'
print(f"Checking WSA version arch={arch} release_type={release_name}", flush=True)
with open(Path.cwd().parent / ("xml/GetCookie.xml"), "r") as f:
    cookie_content = f.read()

out = requests.post(
    'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
    data=cookie_content,
    headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
    verify=False
)
doc = minidom.parseString(out.text)
cookie = doc.getElementsByTagName('EncryptedData')[0].firstChild.nodeValue

with open(Path.cwd().parent / "xml/WUIDRequest.xml", "r") as f:
    cat_id_content = f.read().format(cookie, cat_id, release_type)

out = requests.post(
    'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
    data=cat_id_content,
    headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
    verify=False
)

doc = minidom.parseString(html.unescape(out.text))

filenames = {}
for node in doc.getElementsByTagName('Files'):
    filenames[node.parentNode.parentNode.getElementsByTagName(
        'ID')[0].firstChild.nodeValue] = f"{node.firstChild.attributes['InstallerSpecificIdentifier'].value}_{node.firstChild.attributes['FileName'].value}"
    pass

identities = []
for node in doc.getElementsByTagName('SecuredFragment'):
    filename = filenames[node.parentNode.parentNode.parentNode.getElementsByTagName('ID')[
        0].firstChild.nodeValue]
    update_identity = node.parentNode.parentNode.firstChild
    identities += [(update_identity.attributes['UpdateID'].value,
                    update_identity.attributes['RevisionNumber'].value, filename)]

with open(Path.cwd().parent / "xml/FE3FileUrl.xml", "r") as f:
    file_content = f.read()

for i, v, f in identities:
    if re.match(f"MicrosoftCorporationII\.WindowsSubsystemForAndroid_.*\.msixbundle", f):
        new_version = re.findall(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", f)[0]
        released_version = re.findall(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", released_version)[0]
        if new_version != released_version:
            sys.exit()
        else:
            sys.exit("Same version")
    else:
        continue

sys.exit("WSA version not found")
