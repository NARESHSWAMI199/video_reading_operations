import requests
import os
from urllib.parse import urlparse

url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4" 
def is_downloadable(url):
    content_type = requests.head(url).headers.get('content-type')
    if 'video' in content_type:
        return True
    return False

a = urlparse(url)
if is_downloadable(url):
    r = requests.get(url, allow_redirects=True)
    open(os.path.basename(a.path), 'wb').write(r.content)
else:
    print('Sorry this is not a exact file location.')


