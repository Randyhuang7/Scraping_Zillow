from lxml import html
from lxml import etree
import requests
import csv
import sys

# sold->selling
#MissionUrl = 'http://www.zillow.com/homes/recently_sold/Syracuse-NY-13210/house,mobile,land_type/63017_rid/0-199919_price/0-703_mp/globalrelevanceex_sort/43.080235,-76.038008,42.98236,-76.210013_rect/12_zm/'
#MissionUrl = 'http://www.zillow.com/homes/for_sale/Syracuse-NY-13210/house,mobile,land_type/63017_rid/0-200043_price/0-707_mp/globalrelevanceex_sort/43.077979,-76.045389,42.984621,-76.202803_rect/12_zm/0_mmm/'
zillowid = 'X1-ZWz1fd8gn90vm3_376md'
FieldDict = ['Zpid', 'Address', 'Lattitude', 'Longitude', 'Taxassement', 'FinishedsqFT',
             'Bathroom', 'Bedroom', 'ListType', 'LastSoldDate', 'LastSoldPrice', 'Price']
Profiles = []
xmlItemList = []


def FetchRawPages(url):  # Fetch all pages in Raw file
    raw = []
    Idx = 0
    Next = True

    while Next:
        raw.append(requests.get(url))
        ttree = html.fromstring(raw[Idx].content)
        if len(ttree.xpath('//a[@class="off"]/text()')) > 0:
            url = 'http://www.zillow.com' + \
                ttree.xpath('//a[@class="off"]/@href')[0]
            Idx = Idx + 1
        else:
            Next = False
    print(Idx + 1, 'pages fetched!')
    return raw


def NewProfile():  # Create Now Node
    Newnode = ['n/a', 'n/a', 'n/a', 'n/a', 'n/a',
               'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a']
    return Newnode


def TransAddress(address):  # Dispalce Space to + in Address
    current = 0
    for letter in address:
        if letter == ' ':
            address = address[:current] + '+' + address[current + 1:]
        current = current + 1
    return address


if len(sys.argv) > 1:
    Pages = FetchRawPages(sys.argv[1])
else:
    print("Please input URL")
    sys.exit()
#Pages = FetchRawPages(MissionUrl)
if len(sys.argv) > 2:
    zillowid = sys.argv[2]
    print(zillowid)

for i in range(0, len(Pages)):  # to get all list itmes' xml into the xmlItemList
    tree = html.fromstring(Pages[i].content)
    itemsroot = tree.xpath('//ul[@class="photo-cards"]')
    for item in itemsroot[0].findall('li'):
        if item.find('article') is not None:
            xmlItemList.append(item)

print(len(xmlItemList), 'items found.')

for item in xmlItemList:  # to create the final profile list
    node = NewProfile()
    node[0] = item.find('./article').get('data-zpid')  # zpid
    address = item.find(
        './article/div[@class="zsg-photo-card-content zsg-aspect-ratio-content"]/span[@itemprop="address"]/span[@itemprop="streetAddress"]').text
    node[1] = TransAddress(address)  # address
    node[2] = item.find(
        './article/div[@class="zsg-photo-card-content zsg-aspect-ratio-content"]/span[@itemprop="geo"]/meta[@itemprop="latitude"]').get('content')
    node[3] = item.find(
        './article/div[@class="zsg-photo-card-content zsg-aspect-ratio-content"]/span[@itemprop="geo"]/meta[@itemprop="longitude"]').get('content')
    Status = item.find(
        './article/div[@class="zsg-photo-card-content zsg-aspect-ratio-content"]/div[@class="zsg-photo-card-caption"]//span[@class="zsg-photo-card-status"]/span').get('class')
    if Status == 'zsg-icon-for-sale':
        node[8] = 'Selling'
        node[11] = item.find(
            './article/div[@class="zsg-photo-card-content zsg-aspect-ratio-content"]/div[@class="zsg-photo-card-caption"]//span[@class="zsg-photo-card-price"]').text
    else:
        node[8] = 'Sold ot Others'
    Profiles.append(node)
#	print(node[0], node[1], node[2],node[3],node[8],node[11])

print(len(Profiles), 'profiles filled.')
ZipCode = tree.xpath('//span[@itemprop="postalCode"]')[0].text
index = 0

for A in Profiles:  # call API and complete Profiles
    request = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?zws-id=' + \
        zillowid + '&address=' + A[1] + '&citystatezip=' + ZipCode
    ItemInfo = requests.get(request)
    Itree = html.fromstring(ItemInfo.content)
    A[4] = Itree.xpath('.//taxassessment/text()')
    A[5] = Itree.xpath('.//finishedsqft/text()')
    A[6] = Itree.xpath('.//bathrooms/text()')
    A[7] = Itree.xpath('.//bedrooms/text()')
    A[9] = Itree.xpath('.//lastsolddate/text()')
    A[10] = Itree.xpath('.//lastsoldprice/text()')
    for i in range(4, 11):
        if i != 8:
            if A[i]:
                Profiles[index][i] = A[i][0]
            else:
                Profiles[index][i] = 'n/a'
    # print(Profiles[index],index)
    index = index + 1

print(index, 'profiles completed.')

# test one item
"""request = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?zws-id='+zillowid+'&address='+Profiles[0][1]+'&citystatezip='+ZipCode
ItemInfo = requests.get(request)
Itree = html.fromstring(ItemInfo.content)
Profiles[0][4] = Itree.xpath('.//taxassessment/text()')
Profiles[0][5] = Itree.xpath('.//finishedsqft/text()')
Profiles[0][6] = Itree.xpath('.//bathrooms/text()')
Profiles[0][7] = Itree.xpath('.//bedrooms/text()')
Profiles[0][9] = Itree.xpath('.//lastsolddate/text()')
Profiles[0][10] = Itree.xpath('.//lastsoldprice/text()')
for i in range(4,11):
	if i != 8:
		if  Profiles[0][i]:
			Profiles[0][i] = Profiles[0][i][0]
		else :
			Profiles[0][i] = 'n/a'
print(Profiles[0])"""

# Write into CSV file
f = open(ZipCode + '.csv', 'wt')
try:
    index = 0
    writer = csv.writer(f)
    writer.writerow(('Zpid', 'Lattitude', 'Longitude', 'Taxassement', 'FinishedsqFT',
                     'Bathroom', 'Bedroom', 'ListType', 'LastSoldDate', 'LastSoldPrice', 'Price'))
    for A in Profiles:
        w = True 
        for i in range(4,11):
            if i < 8:
                if A[i] == 'n/a':
                    w = False
                    break
            elif i > 8 and A[i] == 'Sold ot Others':
                if A[i] == 'n/a':
                    w = False
                    break
        if A[8] == 'Selling':
            A[11] = A[11][1:]
        if w:
            writer.writerow((A[0], A[2], A[3], A[4], A[5], A[6],
                         A[7], A[8], A[9], A[10], A[11],))
            index = index + 1
    print('total', index, 'row')
finally:
    f.close()
