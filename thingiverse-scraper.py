#!/usr/bin/python3

# Thingiverse* exporter
# by Carlos Garcia Saura (http://carlosgs.es)
# CC-BY-SA license (http://creativecommons.org/licenses/by-sa/3.0/)
# https://github.com/carlosgs/export-things
# *Unofficial program, not associated with Thingiverse
# Use at your own risk!

# Modules
import requests
from bs4 import BeautifulSoup
import os
import re
import urllib.request, urllib.parse, urllib.error
import time
import sys

#thingID = sys.argv[1]
thingID = re.findall('^.*thing:(.*)$', sys.argv[1])[0]

downloadFiles = True # If set to false, will link to original files instead of downloading them
redownloadExistingFiles = False # This saves time when re-running the script in long lists (but be careful, it only checks if file already exists -not that it is good-)

url = "https://www.thingiverse.com"

# Helper function to create directories
def makeDirs(path):
    try:
        os.makedirs(path)
    except:
        return -1
    return 0

# Helper function to perform the required HTTP requests
def httpGet(page, filename=False, redir=True):
    if filename and not redownloadExistingFiles and os.path.exists(filename):
        return [] # Simulate download OK for existing file
    try:
        r = requests.get(page, allow_redirects=redir)
    except:
        time.sleep(10)
        return httpGet(page, filename, redir)
    if r.status_code == 404:
        print('This project does not have an associated ZIP file.')
        return -1
    if r.status_code != 200:
        print((r.status_code))
        return -1
    if not filename:
        # Remove all non ascii characters
        return r.content.decode('ascii', 'ignore')
    else:
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(512):
                fd.write(chunk)
            fd.close()
        return r.history

res = httpGet(url + "/thing:" + thingID, redir=False)
if res == -1:
    print(("Error while downloading " + thingID))
    exit()

soup = BeautifulSoup(res, "html.parser")

thingTitle = soup.find(property='og:title')['content']
thingDescription = soup.find(property='og:description')['content']
thingImageURL = soup.find(property='og:image')['content']
thingImageName = re.findall(".*\/(.*\..*)", thingImageURL)[0]

folder = str(thingID) + " - " + "-".join(re.findall("[a-zA-Z0-9]+", thingTitle))
print('Creating folder: \t\t\'', folder, '\'')
makeDirs(folder)

print('Fetching featured image: \t\'', thingImageName, '\'')
thingImage = httpGet(thingImageURL, folder + "/" + thingImageName)

print('Fetching ZIP file.')
thingZip = httpGet(url + "/thing:" + thingID + "/zip", folder + "/" + thingID + ".zip")

#thingInstructions = soup.find('span', {'id': re.compile('Print Settings')})

with open(folder + "/README.md", 'w') as fd:
    fd.write("#adamhurm - thingiverse scraper 0.2")
    fd.write("\n===============\n")
    fd.write(thingTitle)
    fd.write("\n-\n")
    fd.write(thingDescription)

print('Successfully downloaded.')


'''

try:
    header_data = res_xml.findAll("div", { "class":"thing-header-data" })[0]
    title = str(header_data.h1.text.encode('utf-8', 'ignore'))
except:
    title = str(res_xml.findAll("title")[0].text.encode('utf-8', 'ignore'))

title = re.sub("\[[^\]]*\]","", title) # Optional: Remove text within brackets from the title
title = title.strip()

folder = "-".join(re.findall("[a-zA-Z0-9]+", title)) # Create a clean title for our folder
print(folder)

makeDirs(folder) # Create the required directories
makeDirs(folder + "/img")


description = res_xml.findAll("div", { "id":"description" })
if description:
    description = "".join(str(item) for item in description[0].contents) # Get the description
    description = description.strip()
else:
    description = "None"

instructions = res_xml.findAll("div", { "id":"instructions" })
if instructions:
    instructions = "".join(str(item) for item in instructions[0].contents) # Get the instructions
    instructions = instructions.strip()
else:
    instructions = "None"

license = res_xml.findAll("div", { "class":"license-text" })
if license:
    license = myGetText(license[0]) # Get the license
else:
    license = "CC-BY-SA (default, check actual license)"



tags = res_xml.findAll("div", { "class":"thing-info-content thing-detail-tags-container" })
if tags:
    tags = myGetText(tags[0]) # Get the tags
else:
    tags = "None"
if len(tags) < 2: tags = "None"



header = res_xml.findAll("div", { "class":"thing-header-data" })
if header:
    header = myGetText(header[0]) # Get the header (title + date published)
else:
    header = "None"
if len(header) < 2: header = "None"


files = {}
for file in res_xml.findAll("div", { "class":"thing-file" }): # Parse the files and download them
    fileUrl = url + str(file.a["href"])
    fileName = str(file.a["data-file-name"])
    filePath = folder + "/" + fileName
    if downloadFiles:
        print(("Downloading file ( " + fileName + " )"))
        httpGet(fileUrl, filePath)
    else:
        print(("Skipping download for file: " + fileName + " ( " + fileUrl + " )"))

    filePreviewUrl = str(file.img["src"])
    filePreviewPath = filePreviewUrl.split('/')[-1]
    filePreview = folder + "/img/" + filePreviewPath
    print(("-> Downloading preview image ( " + filePreviewPath + " )"))
    httpGet(filePreviewUrl, filePreview)

    files[filePath] = {}
    files[filePath]["url"] = fileUrl
    files[filePath]["name"] = fileName
    files[filePath]["preview"] = filePreviewPath

gallery = res_xml.findAll("div", { "class":"thumbs-wrapper axis-vertical" })[0]
images = []
for image in gallery.findAll("div", { "class":"thumb" }): # Parse the images and download them
    imgUrl = str(image["data-large-url"])
    imgName = imgUrl.split('/')[-1]
    imgFile = folder + "/img/" + imgName
    print(("Downloading image ( " + imgName + " )"))
    httpGet(imgUrl, imgFile)
    images.append(imgName)

# Write in the page for the thing
with open(folder + "/README.md", 'w') as fd: # Generate the README file for the thing
    fd.write("#adamhurm - thingiverse scraper 0.2")
    fd.write("\n===============\n")
    fd.write(thingTitle)
    if len(images) > 0:
        fd.write('\n\n![Image](img/' + urllib.parse.quote(images[0]) + ')\n\n')
    fd.write("Description\n--------\n")
    fd.write(thingDescription)
    fd.write("\n\nInstructions\n--------\n")
    fd.write(instructions)

    fd.write("\n\nFiles\n--------\n")
    for path in list(files.keys()):
        file = files[path]
        fileurl = file["url"]
        if downloadFiles:
            fileurl = file["name"]
        fd.write('[![Image](img/' + urllib.parse.quote(file["preview"]) + ')](' + file["name"] + ')\n')
        fd.write(' [ ' + file["name"] + '](' + fileurl + ')  \n\n')

    if len(images) > 1:
        fd.write("\n\nPictures\n--------\n")
        for image in images[1:]:
            fd.write('![Image](img/' + urllib.parse.quote(image) + ')\n')

    fd.write("\n\nTags\n--------\n")
    fd.write(tags + "  \n\n")

    fd.write("  \n\nLicense\n--------\n")
    fd.write(license + "  \n\n")

print("\n\nIt's done!! Keep knowledge free!! Au revoir Thingiverse!!\n")
'''
