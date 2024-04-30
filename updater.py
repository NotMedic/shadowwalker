from m5stack import lcd
from wifiCfg import autoConnect
from urequests import request
import json

BASE_URL = 'https://raw.githubusercontent.com/NotMedic/shadowwalker/'
BRANCH = 'main/'

def fetch_current_version():
    versionurl = BASE_URL + BRANCH + 'version.json'
    req = request(method='GET', url=versionurl, headers={'Content-Type':'text/html'})
    return json.loads(req.text)

def get_installed_version():
    try:
        with open('version.json', 'r') as f:
            return json.loads(f.read())['version']
    except Exception as e:
        return 0

def download_file(file):
    file_url = BASE_URL + BRANCH + file
    print('Downloading ' + file_url)
    lcd.clear()
    lcd.print('Downloading\n' + file, 0, 0)
    response = request(method='GET', url=file_url, headers={'Content-Type':'text/html'})
    with open(file, 'wb') as f:
        f.write(response.content)

def update_version_file(req_text):
    with open('version.json', 'w') as f:
        f.write(req_text)

def update(force=False, branch='main'):
    global BRANCH
    lcd.setRotation(lcd.PORTRAIT_FLIP)
    if autoConnect(lcdShow=True) == 0:
        print('Connected to WiFi')
        # Ensure branch ends with '/'
        if not branch.endswith('/'):
            branch += '/'

        print('Updating from branch {}'.format(branch))
        BRANCH = branch  # Update BRANCH before fetching current version

        current_version_info = fetch_current_version()  # Now fetches from the correct branch
        current_version = current_version_info['version']
        current_files = current_version_info['contents']

        if force:
            installed_version = 0
        else:
            installed_version = get_installed_version()

        print('Installed version: {}'.format(installed_version))

        if current_version != installed_version:
            print('Updating to version {}'.format(current_version))
            for file in current_files:
                download_file(file)
            update_version_file(json.dumps(current_version_info))
        else:
            print('Already up to date')