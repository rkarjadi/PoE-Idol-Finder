from dotenv import load_dotenv

import requests
import pprint
import os
import re
import csv
from collections import defaultdict

pp = pprint.PrettyPrinter(indent = 4)

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')


headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    "User-Agent": f"OAuth {CLIENT_ID}/1.0.0 (contact: rkarjadi@bu.edu)"
}

url = "https://api.pathofexile.com"

def get_stashes():
    '''
        Gets all stashes from PoE API
    '''
    r = requests.get(f"{url}/stash/phrecia", headers=headers).json()

    return r

stash_id = "86223e1254"
substash_ids = ['b82e70b6d7', 'f4f52157e3']

def csv_to_list_of_dicts(csv_file):
    '''
        Reads a CSV file and returns a list of dictionaries
    '''
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data

def get_stash_content(stash_id, substash_id=""):
    '''
        Gets stash content from PoE API
    '''
    r = requests.get(f"{url}/stash/phrecia/{stash_id}/{substash_id}", headers=headers).json()

    return r

def get_items(stash_id):

    stash = get_stash_content(stash_id)['stash']
    idols = [item for item in stash['items'] if 'Idol' in item['typeLine'] and item['rarity'] != 'Unique']

    return idols

def count_mods_by_content_tag(explicit_mods, idol_type):
    """Count explicit mods by content tag based on idol collection."""
    content_tag_counts = defaultdict(int)

    # Get idols based on idol type - create dictionary of affix to content tag
    idols = [idol for idol in csv_to_list_of_dicts('poe-idols.csv') if idol['Idol Type'] == idol_type]
    content_dict = {idol['Stripped Affix']: idol['Content Tag'] for idol in idols}

    # Replace the numbers in mod to #
    for mod in explicit_mods:
        mod = mod.replace('\n', ' ')
        if '%' in mod:
            re_mod = re.sub(r'\d+(\.\d+)?%', r'#%', mod, count=1)

        else:  
            re_mod = re.sub(r'\d+(\.\d+)?', r'#', mod, count=1)

        content_tag = content_dict.get(re_mod)

        if content_tag:
            content_tag_counts[content_tag] += 1

    return dict(content_tag_counts)  # Return the result as a dictionary

def get_content_tags():
    '''
        Gets all content tags possible
    '''
    content_tags = set()
    idols = csv_to_list_of_dicts('poe-idols.csv')

    for idol in idols:
        content_tags.add(idol['Content Tag'])

    return list(content_tags)

def add_content_tags_to_items(items):
    '''
        Gets the content tags of each item and adds it to a contentTag field
    '''

    for item in items:
        idol_type = item['baseType']
        explicit_mods = item['explicitMods']

        content_tags = count_mods_by_content_tag(explicit_mods, idol_type)
        item['contentTags'] = content_tags

    return items

def find_items_by_content_tag(items, content_tag, num_of_mods=0):
    '''
        Finds items with a certain content tag
    '''

    matching_items = []

    for item in items:
        if 'contentTags' in item and content_tag in item['contentTags']:
            if item['contentTags'][content_tag] >= num_of_mods:
                matching_items.append(item)

    return matching_items

items = get_items('b82e70b6d7')
items = add_content_tags_to_items(items)

pp.pprint(items)

tagged_items = find_items_by_content_tag(items, 'Abyss')
pp.pprint(tagged_items)