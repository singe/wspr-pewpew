#!/usr/bin/env python3

from urllib import request
from urllib import parse
from gzip import decompress
import re
import maidenhead
from sys import argv

#Set up cookie jar because the POST gets a 302 with a cookie
opener = request.build_opener(request.HTTPCookieProcessor())
request.install_opener(opener)

#Fetch formID
resp = request.urlopen('http://wsprnet.org/drupal/wsprnet/spotquery')
for x in resp:
  x = x.decode('utf-8')
  if 'form_build_id' in x:
    [formid] = re.findall('name="form_build_id" value="([^"]*)"',x)

url = 'http://wsprnet.org/drupal/wsprnet/spotquery'

data = parse.urlencode({'band' : 7,
'count' : 1000,
#'reporter' : 'ZS6HAK', #This call has seen
'call' : 'ZS6HAK', #People have seen this call
'timelimit' : '1209600', #1209600 is 2 weeks
'sortby' : 'date',
'excludespecial' : '1',
'op' : 'Update',
'form_id' : 'wsprnet_spotquery_form'})
data = data.encode('ascii')

headers = {
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'en-us',
'Accept-Encoding': 'gzip, deflate',
'Referer': 'http://wsprnet.org/drupal/wsprnet/spotquery',
'Content-Type': 'application/x-www-form-urlencoded',
'Connection': 'keep-alive',
'Upgrade-Insecure-Requests': '1',
'Host': 'wsprnet.org'}

req = request.Request(url, data, headers)
resp = request.urlopen(req)
if resp.msg == 'OK':
  #decompress gzip'ed response thanks to our accept header
  respdata = decompress(resp.read())
  respstr = respdata.decode('utf-8')
else:
  exit()

count = -1 
result = ''
for x in respstr.split('\n'):
  #Only keep the actual records, easier than parsing HTML
  if count >= 0 and count <=numspots:
    result = result+'\n'+x
    count+=1
  #Find the number of records
  if ' spots:</p>' in x:
    [numspots] = re.findall('\d+',x)
    numspots = int(numspots)
    count = 0

#Horrible regex's to convert to TSV
tsv = re.sub('<td align[^>]*>',' ',result)
tsv = re.sub('<\/td>','',tsv)
tsv = re.sub('&nbsp;',' ',tsv)
tsv = re.sub('<tr>','',tsv)
tsv = re.sub('<\/tr>','',tsv)
tsv = re.sub('[ ]{2,4}','\t',tsv)
tsv = re.sub('[\t\n ]{2,3}','\n',tsv)
tsv = re.sub('<\/th><th>','\t',tsv)
tsv = re.sub('\n<table><th>','',tsv)
tsv = re.sub('<\/th>','',tsv)
#Convert the time to ISO format so JS can easily consume later
tsv = re.sub('([0-9\-]{10}) ([0-9:]{5})','\g<1>T\g<2>:00Z',tsv)

#Create a list from the TSV
entries = []
for x in tsv.split('\n'):
  entries.append(x.split('\t'))

#Add LatLong from maidenhead grid
entries[0].append('GLat')
entries[0].append('GLong')
entries[0].append('RLat')
entries[0].append('RLong')
for x in entries:
  try:
    [lat,lng] = maidenhead.toLoc(x[5])
    x.append(str(lat))
    x.append(str(lng))
    [lat,lng] = maidenhead.toLoc(x[8])
    x.append(str(lat))
    x.append(str(lng))
  except ValueError: #Ignore header row
    continue

with open(argv[1],'w') as outfile:
  for x in entries:
    outfile.write('\t'.join(x)+'\n')
