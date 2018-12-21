import html.parser as HTMLParser
import re

from bs4 import BeautifulSoup


class IDParser(HTMLParser.HTMLParser):
    """Modified HTMLParser that isolates a tag with the specified id"""

    def __init__(self, id):
        self.id = id
        self.result = None
        self.started = False
        self.depth = {}
        self.html = None
        self.watch_startpos = False
        HTMLParser.HTMLParser.__init__(self)

    def loads(self, html):
        self.html = html
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.started:
            self.find_startpos(None)
        if 'id' in attrs and attrs['id'] == self.id:
            self.result = [tag]
            self.started = True
            self.watch_startpos = True
        if self.started:
            if not tag in self.depth: self.depth[tag] = 0
            self.depth[tag] += 1

    def handle_endtag(self, tag):
        if self.started:
            if tag in self.depth: self.depth[tag] -= 1
            if self.depth[self.result[0]] == 0:
                self.started = False
                self.result.append(self.getpos())

    def find_startpos(self, x):
        """Needed to put the start position of the result (self.result[1])
        after the opening tag with the requested id"""
        if self.watch_startpos:
            self.watch_startpos = False
            self.result.append(self.getpos())

    handle_entityref = handle_charref = handle_data = handle_comment = \
        handle_decl = handle_pi = unknown_decl = find_startpos

    def get_result(self):
        if self.result == None: return None
        if len(self.result) != 3: return None
        lines = self.html.split('\n')
        lines = lines[self.result[1][0] - 1:self.result[2][0]]
        lines[0] = lines[0][self.result[1][1]:]
        if len(lines) == 1:
            lines[-1] = lines[-1][:self.result[2][1] - self.result[1][1]]
        lines[-1] = lines[-1][:self.result[2][1]]
        return '\n'.join(lines).strip()


def get_element_by_id(id, html):
    """Return the content of the tag with the specified id in the passed HTML document"""
    parser = IDParser(id)
    parser.loads(html)
    return parser.get_result()


def get_element_by_class(class_name, some_html, object_type):
    # parse the html
    soup = BeautifulSoup(some_html, features="lxml")
    # find a list of all span elements
    objects = soup.find_all(object_type, {'class': class_name})
    if object_type == "span":
        prices = [re.findall(r'£+[0-9,]*.[0-9]{2}', x.string) for x in objects]
    else:
        prices = [re.findall(r'£ +[0-9,]*.[0-9]{2}', x.text) for x in objects]
    prices_cleaned = [
        str(x)
        .replace(",", "")
        .replace("'", "")
        .replace("[", "")
        .replace("]", "")
        .replace("£ ", "")
        .replace("£", "")
        for x in prices
    ]
    prices_cleaned = [x.replace("£", "") for x in prices_cleaned]
    flattened_array = [float(x) for x in prices_cleaned if x]
    return flattened_array


if __name__ == '__main__':
    import urllib2

    some_html = urllib2.urlopen('http://www.youtube.com/watch?v=BQ80NtYmktQ').read().decode('utf8')
    print(get_element_by_id('eow-description', some_html))
