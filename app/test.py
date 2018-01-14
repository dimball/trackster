import requests
import xml.etree.ElementTree as etree
response = requests.get('http://fatso.diskstation.me:32400/library/sections?X-Plex-Token=7R4zqZsjqbdixgHni9yH')
tree = etree.fromstring(response.content)
for child in tree:
    if child.attrib['type'] == 'artist':
        print(child.attrib['key'])
# print(tree)
# # root = tree.getroot()
# # for child in root:
# #     print(child)