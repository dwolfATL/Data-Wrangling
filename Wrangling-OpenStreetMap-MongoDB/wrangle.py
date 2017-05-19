# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json
"""
@title: Clean and reshape OSM data
@author: DWolf

This function will clean street name abbreviations and amenity types along
with reshaping the data into JSON format for loading into MongoDB

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  is turned into jSON:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

"""

# regex for problem characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Will add these fields to each node
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

# Acceptable street types
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Circle", "Northeast", "Northwest", "Southeast",
            "Southwest", "Way", "North", "South", "East", "West", "Suite"]

# Street type mapping
addr_mapping = { "St.": "Street", "Ave": "Avenue", "Ave.": "Avenue", "Rd.": "Road",
            "Rd": "Road", "RD": "Road", "Blvd": "Boulevard", "Dr": "Drive", "NE": "Northeast",
            "N.W.": "Northwest", "NW": "Northwest", "SE": "Southeast", "N": "North",
            "E": "East", "N.": "North", "E.": "East" }

# Amenity mapping
amenity_mapping = { "Taco Mac" : "restaurant" , "Subway" : "fast_food" , 
                    "Landmark Diner" : "restaurant" , "McDonald's" : "fast_food" }

attr_fixing = { "Walgreen's" : "Walgreens" , "social_centre" : "social_center" }

# dicts that track cleaning
expected_count = {}
fixed_street_count = {}
fixed_attr_count = {}

# Function to remove abbreviations throughout the street name
def update_street(street):
    
    street_split = street.strip().split(" ")
    new_street = ""
    
    for street_word in street_split:
        better_word = street_word
        # If the word is in the addr_mapping table, we need to update it
        if street_word in addr_mapping:
            better_word = addr_mapping[street_word]
        # Append it back to the new street string
        new_street += better_word + " "
        # Track the changes
        if better_word not in fixed_street_count and better_word != street_word:
            fixed_street_count[better_word] = 1
        elif better_word != street_word:
            fixed_street_count[better_word] += 1    
        if street_word not in expected_count and street_word in expected:
            expected_count[street_word] = 1
        elif street_word in expected:
            expected_count[street_word] += 1
        
    return new_street.strip()

# Function to update the amenity and name for some nodes
def update_amenity(node):
    
    if "amenity" in node and "name" in node:
        if node["name"] in amenity_mapping and node["amenity"] != amenity_mapping[node["name"]]:
            node["amenity"] = amenity_mapping[node["name"]]
            # Track the stats on the changes that are made
            if node["name"] in fixed_attr_count:
                fixed_attr_count[node["name"]] += 1
            else:
                fixed_attr_count[node["name"]] = 1
    # Return the node with the potentially updated amenity
    return node

# Shape the OSM file nodes into JSON format for MongoDB
def shape_element(element):
    node = {}
    created_array = {}
    address_array = {}
    node_array = []
    k_value = ""
    v_value = ""
    # Only process the element if it is a node or a way
    if element.tag == "node" or element.tag == "way":
        node['type'] = element.tag # Add "node" or "way" as the type of the node
        if 'id' in element.attrib:
            node['id'] = element.attrib['id']
        if 'visible' in element.attrib:
            node['visible'] = element.attrib['visible']
        for attribute in CREATED:
            # Check for the attribute and then add it to the created array
            if attribute in element.attrib:
                created_array[attribute] = element.attrib[attribute]
        if created_array != {}:
            node['created'] = created_array
        if 'lat' in element.attrib and 'lon' in element.attrib:
            node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
        # Iterate through the children that have a tag called "tag"
        for tag in element.iter("tag"):
            if 'k' in tag.attrib:
                k_value = tag.attrib['k']
            if 'v' in tag.attrib:
                v_value = tag.attrib['v']
            # Only process the k_value if it does not have any problem characters
            if problemchars.search(k_value) == None:
                if k_value.startswith("addr:"):
                    k_value = k_value.replace("addr:","")
                    # If this is a street, send it to the update_street()                    
                    if k_value == "street":
                        v_value = update_street(v_value)
                    if ":" not in k_value:
                        address_array[k_value] = v_value
                # Scenarios where k does not start with "addr:"
                else:
                    # Check if this is one of the attributes that needs fixing                    
                    if v_value in attr_fixing:
                        v_value = attr_fixing[v_value]
                        if v_value in fixed_attr_count:
                            fixed_attr_count[v_value] += 1
                        else:
                            fixed_attr_count[v_value] = 1
                    node[k_value] = v_value
        if address_array != {}:
            node['address'] = address_array
        # Special scenario for node refs when the element tag is way
        if element.tag == "way":
            for nd in element.iter("nd"):
                if 'ref' in nd.attrib:
                    node_array.append(nd.attrib['ref'])
        if node_array != []:
            node['node_refs'] = node_array
        # Ensure a matching relationship between amenity and name
        node = update_amenity(node)
        return node
    else:
        return None

# write the results to JSON
def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+",\n")
                else:
                    fo.write(json.dumps(el) + ",\n")
    return data

data = process_map('atlanta_buckhead_georgia.osm', False)
#pprint.pprint(data)

