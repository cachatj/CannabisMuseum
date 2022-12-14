#! /usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import csv
import json
import math
import time
import readline
from urllib.parse import urlparse

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError
    from urllib.parse import urlparse
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen, URLError, HTTPError

'''
Extract top-level metadata and element_texts from items returned by
Omeka 2.x API request, and then write to a CSV file. Intended for
requests to items, collections, element sets, elements, files, tags, exhibits, and exhibit pages.

Based on Caleb McDaniel's original Python CSV file generator: https://github.com/wcaleb/omekadd
'''

try:
    input = raw_input
except NameError:
    pass

try:
    unicode
    py2 = True
except NameError:
    unicode = str
    py2 = False

endpoint = 'http://cannabismuseum.com/omeka/api'
while not endpoint:
    endpoint = input('Enter your Omeka API endpoint\n')
apikey = input('If you are using an API key, please enter it now. Otherwise press Enter.\n')
if not apikey: 
    apikey = 'a67853bc6cad9fc127d3c872d6c1e706d3b5d7d3'

available_resources = ['items', 'files', 'elements', 'element_sets', 'tags', 'exhibits', 'exhibit_pages']
for resource in available_resources:
    print('Exporting ' + resource)
    def request(query={}):
        url = endpoint + "/" + resource
        if apikey is not None:
            query["key"] = apikey
        url += "?" + urlencode(query)

        response = urlopen(url)
        return response.info(), response.read()
    def unicodify(v):
        if type(v) is list or type(v) is dict:
            return None
        if type(v) is bool or type(v) is int:
           return unicode(v)
        return v

    def get_all_pages(pages):
        global data
        page = 1
        while page <= pages:
            print('Getting results page ' + str(page) + ' of ' + str(pages) + ' ...')
            response, content = request({'page': str(page), 'per_page': '50'})
            data.extend(json.loads(content))
            page += 1
            time.sleep(2)

    # make initial API request; get max pages
    response, content = request()
    pages = int(math.ceil(float(response['omeka-total-results'])/50))
    pages = 200

    # declare global variables; get all pages
    fields = []
    data = []
    get_all_pages(pages)
    csv_rows = []

    for D in data:
        csv_row = {}

        for k, v in D.items():
            if k == 'tags':
                tags = [ tag['name'] for tag in v ]
                csv_row['tags'] = ','.join(tags)
            elif k == 'element_texts':
                for element_text in v:
                    csv_row[element_text['element']['name']] = element_text['text']
            elif k == 'page_blocks':
                text = [ block['text'] for block in v ]
                csv_row['Text'] = ' | '.join(filter(None, text))
            elif k == 'owner_id':
                csv_row['owner_id'] = unicodify(v['id'])
            elif type(v) is dict:
                for subkey, subvalue in v.items():
                    subvalue_string = unicodify(subvalue)
                    if subvalue_string is not None:
                        csv_row[k + '_' + subkey] = subvalue_string
                continue;
            elif type(v) is list or v is None:
                continue;
            else:
                csv_row[k] = unicodify(v)

        for k in csv_row.keys():
            if k not in fields: fields.append(k)
        csv_rows.append(csv_row)

    if (py2):
        o = open(resource + '_output.csv', 'w')
        c = csv.DictWriter(o, [f.encode('utf-8', 'replace') for f in sorted(fields)], extrasaction='ignore') 
        c.writeheader()
        for row in csv_rows:
            c.writerow({k:v.encode('utf-8', 'replace') for k,v in row.items() if isinstance(v, unicode)})
    else:
        o = open(resource + '_output.csv', 'w', encoding = 'utf-8')
        c = csv.DictWriter(o, sorted(fields), extrasaction='ignore')
        c.writeheader()
        for row in csv_rows:
            c.writerow(row)
    o.close()
    print('File created: ' + resource + '_output.csv')
