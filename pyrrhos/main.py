import re
import os
from bs4 import BeautifulSoup as bs


class Page:
    titles = []
    urls = []

    def __init__(self, title, auto_images=False, img_class='character'):
        self.title = title
        Page.titles.append(title)

        self.url = remove_articles(self.title).split()[0].lower()
        if self.url == 'geographical': self.url = 'geography'
        if self.url == 'political': self.url = 'politics'
        Page.urls.append(self.url)
        self.full_url = self.url + '.html'

        self.vocab = []
        self.header_text = ""
        self.main_text = ""

        if auto_images:
            self.add_images(self.title.lower(), img_class=img_class)

    def maintenance(self, external_links):
        self.main_text = self.main_text.replace('</ul>', '</ul><p><br /></p>')
        for word in external_links:
            self.header_text = add_links(self.header_text, word, external_links[word])
            self.main_text = add_links(self.main_text, word, external_links[word])

    def cross_reference(self, other_page):
        if self == other_page:
            return

        term_map = {}
        for word in sorted(other_page.vocab, key=len)[::-1]:
            clean_word = post_clean_term(word)
            for word2 in self.vocab:
                clean_word2 = post_clean_term(word2)
                if clean_word in clean_word2:
                    term_encoding = str(hash(clean_word2))
                    term_map[clean_word2] = term_encoding
                    self.main_text = self.main_text.replace(clean_word2, term_encoding)

            self.main_text = add_links(self.main_text, word, other_page.full_url)

        for term in term_map:
            self.main_text = self.main_text.replace(term_map[term], term)


    def write(self):
        src = HTML_String()

        # Head
        src.write(f'<title>Pyrrhos - {self.url.capitalize()}</title>')

        # Header
        src.write('</head><body><a name="top"></a>')
        src.write('<h1>Pyrrhos</h1><h2>')

        src.write_list([f'<a href="{url + ".html"}">{url.upper()}</a> ' if self.url != url else f'{url.upper()} ' for url in Page.urls])
        src.write('</h2>')
        src.write(self.header_text)

        # Table of Contents
        if len(self.vocab) > 0:
            src.write('<toc><li><strong>CONTENTS</strong></li>')
            if self.main_text.count('<ul') >= 2:
                table_terms = [self.vocab[0]]
                for term in re.findall("</ul>(.*?)<ul>", self.main_text.replace('\n', '')):
                    table_terms.append(re.search("<strong>(.*)</strong>", term).group(1))
            else:
                table_terms = self.vocab
            src.write_list([f'<li><blockquote><a href="#{word}">{word}</a></blockquote></li>' for word in table_terms])
            src.write('</toc>')

        # Main text
        src.write(self.main_text)
        src.finish()

        with open('html/' + self.full_url, 'w', encoding='UTF-8') as f:
            f.write(src.prettify())

    def add_images(self, image_folder, img_class='character'):
        file_path = './images/' + image_folder
        images = [f for f in sorted(os.listdir(file_path)) if (f.endswith('.png') or f.endswith('.jpg'))]
        descriptions = [f for f in os.listdir(file_path) if f.endswith('.txt')]
        for source in images:
            self.main_text += f'<img class="{img_class}" src=".{file_path}/{source}" alt="picture here">'
            desc = os.path.splitext(source)[0] + '.txt'
            if desc in descriptions:
                with open(file_path + '/' + desc) as f:
                    self.main_text += f'<cap>{f.readlines()[0]}</cap>'


class HTML_String:
    def __init__(self):
        self.raw_string = "<!DOCTYPE html><html><head>"
        self.raw_string += ('<link rel="stylesheet" href="../css/header.css">'
                            '<link rel="stylesheet" href="../css/body.css">')

    def write(self, s):
        self.raw_string += s

    def write_list(self, l):
        self.raw_string += ''.join(l)

    def finish(self):
        self.write('<ftr>')
        self.write('<p><a href="#top">Back to top</a></p>')
        self.write('<p><a href="https://github.com/aneziac/aneziac.github.io/tree/master/pyrrhos">Source code</a></p>')
        self.write('</ftr>')
        self.write('</body></html>')
        self.sub_anchors()

    # By default, prettify starts a newline for anchors, which messes up all links
    # To solve, links are substituted for hashes, then prettify is executed, then the hashes are substituted back into links
    # Somehow the > character after the link is getting converted to '&gt;'
    # To do: investigate this issue

    def sub_anchors(self):
        self.raw_string = self.raw_string.replace('<a', str(hash('<a')))
        self.raw_string = self.raw_string.replace('</a>', str(hash('</a>')))

    def resub_anchors(self, string):
        string = string.replace(str(hash('<a')), '<a')
        string = string.replace(str(hash('</a>')), '</a>')
        string = string.replace('&gt;', '>')  # what is causing this?
        return string

    def prettify(self):
        soup = bs(self.raw_string, features="html.parser")
        return self.resub_anchors(soup.prettify())


def download_source():
    import gdown
    import pypandoc

    source = 'https://docs.google.com/document/export?format=docx&id=10zOwNbnFIhr0NnuXhmXsRoRdr_eq7BBZ2lnI3Hb8Gw0'
    gdown.download(source, 'pyrrhos.docx', quiet=True)
    pypandoc.convert_file('pyrrhos.docx', 'html', outputfile="raw.html")


def pre_clean_term(term):
    return term.replace(' -', '').replace('<u>', '').replace('</u>', '').rstrip()


def post_clean_term(term): # add brackets
    return remove_articles(re.sub(r"\([^()]*\)", "", term).rstrip(' ()'))


def remove_articles(term):
    split_term = term.split()
    if split_term[0] in ['The', 'A', 'An']:
        return ' '.join(split_term[1:])
    else:
        return term


def add_links(string, substring, link):
    result = string
    clean_substring = post_clean_term(substring)

    for v in [clean_substring,
              clean_substring + 's',
              clean_substring + 'n',
              clean_substring[:-2] + 'an',
              clean_substring + 'ish',
              clean_substring[:-1] + 'ves',
              clean_substring[:-1] + 'ven',
              clean_substring[:-4] + 'ian',
              clean_substring[:-1] + 'ish']:
        for w in [v, v.lower()]:
            for x in [' ' + w + ' ',
                      ' ' + w + ',',
                      ' ' + w + '.',
                      ' ' + w + '!',
                      ' ' + w + ')',
                      ' ' + w + "’",
                      ' ' + w + '?',
                      ' ' + w + '/',
                      '/' + w + ')',
                      '/' + w + '/',
                      '(' + w + '/',
                      '(' + w + ' ',
                      '(' + w + ',',
                      ' ' + w + '\n']:
                result = result.replace(x, x[0] + f'<a href="{link}#{substring}">{w}</a>' + x[-1])

    return result


def build_website():
    pages, page_index = [], 1
    for page_title in ['Home Page',
                       'A Geographical Overview of Pyrrhos',
                       'Political Overview of Pyrrhos',
                       'The Races of Pyrrhos',
                       'Religion',
                       'Monsters',
                       'Cosmology']:
        pages.append(Page(page_title))

    pages[0].add_images('world', 'cover')

    with open('raw.html', 'r') as f:
        lines = f.readlines()
        current_page = pages[0]

        header_feed = True
        for line in lines:
            line = line.replace('e`', 'è')
            if header_feed and True in [t in line for t in ['<strong', '<ol', '<em', '<ul']]:
                header_feed = False
            if '<strong>' in line:
                for title in Page.titles:
                    if title in line and ' -' not in line:
                        current_page = pages[page_index]
                        page_index += 1
                        header_feed = True
                if current_page.url != 'home':
                    term = re.search("<strong>(.*)</strong>", line)
                    if term is not None:
                        term = pre_clean_term(term.group(1))
                        current_page.main_text += f'<a name="{term}"></a>'
                        if term not in Page.titles:
                            current_page.vocab.append(term)

            if header_feed:
                current_page.header_text += line
            else:
                current_page.main_text += line

    external_links = {
        'Hawaii': 'https://en.wikipedia.org/wiki/Hawaii',
        'Eberron': 'https://eberron.fandom.com/wiki/Eberron_Wiki',
        'House Ghallanda': 'https://eberron.fandom.com/wiki/House_Ghallanda',
        'Switzerland': 'https://en.wikipedia.org/wiki/Switzerland'
    }

    for class_name in ['Barbarian',
                       'Bard',
                       'Cleric',
                       'Druid',
                       'Fighter',
                       'Monk',
                       'Paladin',
                       'Ranger',
                       'Rogue',
                       'Sorcerer',
                       'Warlock',
                       'Wizard',
                       'Artificer']:
        external_links[class_name] = 'https://www.dndbeyond.com/classes/' + class_name.lower()

    world_map = Page('Map', auto_images=True, img_class='map')
    players = Page('Players', auto_images=True)
    npcs = Page('NPCs', auto_images=True)

    pages = pages + [world_map, players, npcs]

    for page in pages:
        page.maintenance(external_links)

    for page1 in pages:
        for page2 in pages:
            page1.cross_reference(page2)
        page1.write()


def main():
    download_source()
    build_website()


main()
