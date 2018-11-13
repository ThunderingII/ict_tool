import re

# print(re.match('\d\w+', '2class'))


import io
import gzip

# content = '0b6f781984b042cd184563c73a091732d67d049d5b396b189a24095b1a948a8ad6e7424924d25ba26471c378659dcddd8bc2121d21bd1a0874cb0df14a9f35511eba880463a5b94c7aec4e6772e3ba036df874cc6cf7c6f1c0ab03bf33f4074a762411bd9cd6ef4b53cb4145a41f7572883ff0e78b18276634ef04c30765f5d5852435931a61649366aac4fb462cdbf2'
# content = content.encode('utf-8')
# buf = io.BytesIO(content)
# print(gzip.decompress(content))

# gf = gzip.GzipFile(fileobj=buf)
# content = gf.read()
# print(content)

# print(isinstance('111', str))
# if [1]:
#     print(1)
# print(2)
#
# d = '\35 > div.f13 > a:nth-child(466) > q'
# print(d.split(':nth-child'))
# print(d.split(':nth-child')[0].rsplit(' > ', 1))
# bf = d.split(':nth-child')
#
# print(bf[0] + ':nth-of-type(' + str(456) + bf[1][bf[1].find(')'):])
# # print(bf[1].find('('))
# # print(bf[1].find(')'))
# print()
# print(d.split(':nth-child'))

from bs4 import BeautifulSoup
from bs4 import Tag

bs = BeautifulSoup(
    '<body>	<div>1</div>	<div>2</div>	<!-- 1111111-->	"1111"	<a>3333</a>	<a>334433</a></body>')
index = 1
for i, c in enumerate(bs.select('body')[0].children):
    if isinstance(c, Tag):
        print(i, c)
        index += 1
