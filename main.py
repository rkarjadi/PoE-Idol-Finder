from dotenv import load_dotenv

import requests
import pprint
import os
import re
from pymongo import MongoClient, UpdateOne
from collections import defaultdict

pp = pprint.PrettyPrinter(indent = 4)

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

client = MongoClient(MONGO_CONNECTION_STRING)
db = client['poe']

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    "User-Agent": f"OAuth {CLIENT_ID}/1.0.0 (contact: rkarjadi@bu.edu)"
}

url = "https://api.pathofexile.com"

# r = requests.get(f"{url}/stash/phrecia", headers=headers).json()
# print(r)

def get_stashes():
    '''
        Gets all stashes from PoE API
    '''
    r = requests.get(f"{url}/stash/phrecia", headers=headers).json()

    return r

stash_id = "86223e1254"
substash_ids = ['b82e70b6d7', 'f4f52157e3']

def get_stash_content(stash_id, substash_id=""):
    '''
        Gets stash content from PoE API
    '''
    r = requests.get(f"{url}/stash/phrecia/{stash_id}/{substash_id}", headers=headers).json()

    return r

def add_items():
    collection = db['items']

    stash = get_stash_content(substash_ids[0])['stash']

    idols = [item for item in stash['items'] if 'Idol' in item['typeLine'] and item['rarity'] != 'Unique']

    # Retrieve existing item IDs from the database
    existing_ids = set(item['id'] for item in collection.find({}, {'id': 1}))
    print(f"Existing IDs: {len(existing_ids)} found.")

    # Filter out items that already exist
    new_idols = [idol for idol in idols if idol['id'] not in existing_ids]
    print(f"New IDs found: {len(new_idols)}")

    # Insert new items in bulk
    if new_idols:
        collection.insert_many(new_idols)
        print(f"Inserted {len(new_idols)} new idols into MongoDB")

    else:
        print("No new idols to insert")

def get_items():
    collection = db['items']

    idols = list(collection.find({}, {'_id': 0}))

    return idols

def count_mods_by_content_tag(explicit_mods, idol_type):
    """Count explicit mods by content tag based on idol collection."""
    collection = db['idols']
    content_tag_counts = defaultdict(int)

    # Get idols based on idol type - create dictionary of affix to content tag
    idols = list(collection.find({'Idol Type': idol_type}, {'_id': 0}))
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
    collection = db['idols']

    content_tags = list(collection.distinct('Content Tag'))

    return content_tags

def add_content_tags_to_items():
    '''
        Gets the content tags of each item and adds it to a contentTag field
    '''
    collection = db['items']

    items = list(collection.find({}))

    for item in items:
        idol_type = item['baseType']
        explicit_mods = item['explicitMods']

        content_tags = count_mods_by_content_tag(explicit_mods, idol_type)
        item['contentTags'] = content_tags

    # Update all items in the database with the new contentTags field
    bulk_updates = [
        {
            'filter': {'_id': item['_id']},
            'update': {'$set': {'contentTags': item['contentTags']}}
        }
        for item in items
    ]

    if bulk_updates:
        result = collection.bulk_write(
            [UpdateOne(update['filter'], update['update']) for update in bulk_updates]
        )

        # Print the results of the bulk write operation
        print(f"Bulk write acknowledged: {result.acknowledged}")
        print(f"Inserted count: {result.inserted_count}")
        print(f"Matched count: {result.matched_count}")
        print(f"Modified count: {result.modified_count}")
        print(f"Deleted count: {result.deleted_count}")
        print(f"Upserted count: {result.upserted_count}")
        print(f"Upserted IDs: {result.upserted_ids}")

def find_items_by_content_tag(content_tag, num_of_mods=0):
    collection = db['items']

    items = list(collection.find({f'contentTags.{content_tag}': {'$gt': num_of_mods}}))

    return items
