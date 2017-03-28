import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint

osm_path = "C:\Users\Leo\Anaconda3\P3 Project OSM\singapore.osm"
test_re = re.compile(r'\d{6}')

def check_pc(osmfile):
    '''Checks if postal codes matches regular expression.
        Adds attributes which do not match to list and returns it.'''
    osm_file = open(osm_path, "r")
    pc_codes = []
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == 'addr:postcode' and not test_re.search(tag.attrib['v']):
                    pc_codes.append(tag.attrib['v'])
    osm_file.close()
    return pc_codes

pprint.pprint(check_pc(osm_path))