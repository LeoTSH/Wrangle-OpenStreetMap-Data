import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

#Set filepath
OSM_PATH = "C:\Users\Leo\Anaconda3\P3 Project OSM\singapore.osm"

#Set mapping
mapping = { "St": "Street",
            "St.": "Street",
            "Rd.": "Road",
            "Rd": "Road",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Dr": "Drive",
            "Dr.": "Drive"
            }

#Set save files
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

#Set regular expressions
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
post_re = re.compile(r'\d{6}')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):

    #Set mapping
    update = { "St": "Street",
            "St.": "Street",
            "Rd.": "Road",
            "Rd": "Road",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Dr": "Drive",
            "Dr.": "Drive"
            }

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        #Iterate through all attributes from node tag
        for attr in element.attrib:
            #If attributes are in FIELDS            
            if attr in node_attr_fields:
                node_attribs[attr] = element.attrib[attr]
        #Iterate through all sub-tags for element
        for sub in element:               
            #Create empty Dict
            node_elements = {}
            #Ignore if k.tag value has problematic chars
            if problem_chars.search(sub.attrib['k']):
                continue
            #If k.tag value matches lower_colon
            elif LOWER_COLON.search(sub.attrib['k']):
                node_elements['id'] = element.attrib['id']
                node_elements['key'] = sub.attrib['k'].split(':', 1)[1]
                node_elements['type'] = sub.attrib['k'].split(':', 1)[0]
                node_elements['value'] = sub.attrib['v']
                if node_elements['key'] == 'street':
                    node_elements['value'] = update_name(sub.attrib['v'], update)
                elif node_elements['key'] == 'postcode':
                    if update_pc(sub.attrib['v']):
                        node_elements['value'] = update_pc(sub.attrib['v'])
                tags.append(node_elements)
            else:
                node_elements['id'] = element.attrib['id']
                node_elements['key'] = sub.attrib['k']
                node_elements['type'] = default_tag_type
                node_elements['value'] = sub.attrib['v']
                tags.append(node_elements)
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for attr in element.attrib:
            #If attributes are in FIELDS
            if attr in way_attr_fields:
                way_attribs[attr] = element.attrib[attr]
            position = 0    
        for sub in element:
            #Create empty Dict
            way_elements = {}
            way_ref = {}
            start_list = []
            if sub.tag == 'nd':
                way_ref['id'] = element.attrib['id']
                way_ref['node_id'] = sub.attrib['ref']
                way_ref['position'] = position
                way_nodes.append(way_ref)
                position += 1
            if sub.tag == 'tag':
                if problem_chars.search(sub.attrib['k']):
                    continue
                #If k.tag value matches lower_colon
                elif LOWER_COLON.search(sub.attrib['k']):
                    way_elements['id'] = element.attrib['id']
                    way_elements['key'] = sub.attrib['k'].split(':', 1)[1]
                    way_elements['type'] = sub.attrib['k'].split(':', 1)[0]
                    way_elements['value'] = sub.attrib['v']
                    if way_elements['key'] == 'street':
                        way_elements['value'] = update_name(sub.attrib['v'], update)
                    elif way_elements['key'] == 'postcode':
                        way_elements['value'] = update_pc(sub.attrib['v'])
                    tags.append(way_elements)
                else:
                    way_elements['id'] = element.attrib['id']
                    way_elements['key'] = sub.attrib['k']
                    way_elements['type'] = default_tag_type
                    way_elements['value'] = sub.attrib['v']
                    tags.append(way_elements)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

# ================================================== #
#               Helper Functions                     #
# ================================================== #

#Writer function
class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

#Update street names
def update_name(name, mapping):
    '''
    Args: 
        name: street value of attrib['v']
        mapping: dictionary to replace found string/character
        
    Returns:
        Updated street name'''
    for map in mapping:
        if map in name:
            name = re.sub(r'\b' + map + r'\b\.?', mapping[map], name)
    return name

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
            
#Update postal code based on continous 6-digit format in Singapore
#Searches entire string for match
def update_pc(pc):
    '''
    Args:
        pc: postcode value of attrib['v']
        
    Returns:
        Updated postcode'''
    if post_re.search(pc):
        pc = post_re.search(pc).group()
    return pc

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

# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""
    
    #Write files
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        
        #Set elements
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

def test():
   process_map(OSM_PATH)

if __name__ == '__main__':
    test()