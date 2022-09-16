#! /usr/bin/python

from omekaclient import OmekaClient
from httplib2 import ServerNotFoundError
import csv
import json
import math
import time
import readline
#import urllib.parse
import urllib
from urllib.parse import urlparse

'''
Extract top-level metadata and element_texts from items returned by
Omeka 2.x API request, and then write to a CSV file. Intended for
requests to items, collections, element sets, elements, files, tags, exhibits, and exhibit pages.

Based on Caleb McDaniel's original Python CSV file generator: https://github.com/wcaleb/omekadd
'''

##OMEKA API ENDPOINT http://cannabismuseum.com/omeka/api
##OMEKA ADMIN API KEY a67853bc6cad9fc127d3c872d6c1e706d3b5d7d3 

unicode = str

endpoint = 'http://cannabismuseum.com/omeka/api'
#while not endpoint:
 #   endpoint = raw_input('Enter your Omeka API endpoint\n')
apikey = 'a67853bc6cad9fc127d3c872d6c1e706d3b5d7d3'
#if not apikey:
#    apikey = 'a67853bc6cad9fc127d3c872d6c1e706d3b5d7d3'

available_resources = ['items', 'files', 'elements', 'element_sets', 'tags', 'exhibits', 'exhibit_pages']
for resource in available_resources:
    print('Exporting ' + resource)

    def request(query={}):
        try:
            response, content = OmekaClient(endpoint, apikey).get(resource, None, query)
            if response.status != 200:
                print(response.status, response.reason)
                exit()
            else:
                return response, content
        except ServerNotFoundError:
            print('The server was not found. Please check your endpoint and try again.')
            exit()

    def unicodify(v):
        if type(v) is bool or type(v) is int:
           return str(v)
        else:
           return v

    def get_all_pages(pages):
        global data
        page = 1
        while page <= pages:
            print('Getting results page ' + unicode(page) + ' of ' + unicode(pages) + ' ...')
            response, content = request({'page': unicode(page), 'per_page': '50'})
            data.extend(json.loads(content))
            page += 1
            time.sleep(2)

    def expand(obj):
        keys = obj.keys()
        for k in keys:
            if k in obj:
                expandField(obj, k, v)

    # make initial API request; get max pages
    response, content = request()
    pages = int(math.ceil(float(response['omeka-total-results'])/50))

    # declare global variables; get all pages
    fields = []
    data = []
    get_all_pages(pages)

    for D in data:
        if 'tags' in D and D['tags']:
            tags = [ d['name'] for d in D['tags'] ]
            D['tags'] = ', '.join(tags)
        if 'element_texts' in D:
            for d in D['element_texts']:
                k = d['element']['name']
                v = d['text']
                D[k] = v
        if 'page_blocks' in D:
                text = [ d['text'] for d in D['page_blocks'] ]
                D['Text'] = ' | '.join(filter(None, text))
        for k, v in D.items.copy():
            D[k] = unicodify(v)
            if D[k] and type(v) is dict:
                for key, value in v.items():
                    D[k + '_' + key] = unicodify(D[k][key])
            if type(v) is list or type(v) is dict:
                del D[k] 
            if v == None:
                del D[k]
        for k in list(D):
            if k not in fields: fields.append(k)

    # write to CSV output file using DictWriter instance
    # by default, fill empty cells with 'None'; un-quote None for empty cell
    o = open(resource + '_output.csv', 'w')
    c = csv.DictWriter(o, [f.encode('utf-8', 'replace') for f in sorted(fields)], restval='None', extrasaction='ignore') 
    c.writeheader()
    for D in data:
        c.writerow({k:v.encode('utf-8', 'replace') for k,v in D.items() if isinstance(v, unicode)})

    o.close()
    print('File created: ' + resource + '_output.csv')
