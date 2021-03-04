import re
import os
from bs4 import BeautifulSoup as bs


class Page:
    urls = []

    def __init__(self, title, auto_images=False, img_class='character'):
        self.title = title

        self.url = remove_articles(self.title).split()[0].lower()
        if self.url == 'geographical': self.url = 'geography'
        if self.url == 'political': self.url = 'politics'
        Page.urls.append(self.url)
        self.full_url = self.url + '.html'
        self.tab = self.url.capitalize()
        if self.url == 'npcs': self.tab = 'NPCs'

        self.vocab = []
        self.header_text = ""
        self.main_text = ""

        if auto_images:
            self.add_images(self.title.lower(), img_class=img_class)

    def maintenance(self, external_links):
        self.main_text = self.main_text.replace('</ul>', '</ul><p><br /></p>')

        for word in external_links:
            self.header_text = self.add_links(self.header_text, Term(word), external_links[word], False)
            self.main_text = self.add_links(self.main_text, Term(word), external_links[word], False)

    def cross_reference(self, other_page):
        if self == other_page:
            return

        term_map = {}
        for word in sorted(other_page.vocab, key=lambda term: len(term.short), reverse=True):
            for word2 in self.vocab:
                if word.short in word2.short:
                    term_encoding = str(hash(word2.short))
                    term_map[word2.short] = term_encoding
                    self.main_text = self.main_text.replace(word2.short, term_encoding)

            self.main_text = self.add_links(self.main_text, word, other_page.full_url)

        for term in term_map:
            self.main_text = self.main_text.replace(term_map[term], term)


    def write(self):
        src = HTML_String()

        # Head
        src.write(f'<title>Pyrrhos - {self.tab}</title>')

        # Header <div id="rectangle"></div>
        src.write('</head><body><div id="rectangle"><a name="top"></a>')
        src.write('<h1>Pyrrhos</h1><h2>')

        src.write_list([f'<a href="{url + ".html"}">{url.capitalize()}</a> ' if self.url != url else f'{url.capitalize()} ' for url in Page.urls])
        src.write('</h2></div><div id="main">')
        src.write(self.header_text)

        # Table of Contents
        if len(self.vocab) > 0:
            src.write('<toc class="header"><strong>Contents</strong></toc><toc>')
            if self.main_text.count('<ul') >= 2:
                table_terms = [self.vocab[0]]
                for term in re.findall("</ul>(.*?)<ul>", self.main_text.replace('\n', '')):
                    table_terms.append(Term(re.search("<strong>(.*)</strong>", term).group(1)))
            else:
                table_terms = self.vocab
            src.write_list([f'<li class="toc"><blockquote><a href="#{word.long}">{word.long}</a></blockquote></li>' for word in table_terms])
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

    def add_links(self, string, substring, link, internal=True):
        result = string

        for v in [substring.short,
                substring.short + 's',
                substring.short + 'n',
                substring.short[:-2] + 'an',
                substring.short + 'ish',
                substring.short[:-1] + 'ves',
                substring.short[:-1] + 'ven',
                substring.short[:-4] + 'ian',
                substring.short[:-1] + 'ish']:
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
                        ' ' + w + '-',
                        ' ' + w + '\n']:
                    if internal:
                        result = result.replace(x, x[0] + f'<a href="{link}#{substring.long}">{w}</a>' + x[-1])
                    else:
                        result = result.replace(x, x[0] + f'<a href="{link}">{w}</a>' + x[-1])

        return result


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
        self.write('</div><ftr>')
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


class Website:
    def __init__(self, page_titles=[]):
        self.pages, self.page_titles = [], page_titles
        for page_title in self.page_titles:
            self.pages.append(Page(page_title))

    def read_source(self, source_file):
        page_index = 0
        with open(source_file, 'r') as f:
            lines = f.readlines()
            current_page = self.pages[page_index]

            header_feed = True
            for line in lines:
                line = line.replace('e`', 'è')
                if header_feed and True in [t in line for t in ['<strong', '<ol', '<em', '<ul']]:
                    header_feed = False

                if '<strong>' in line:
                    for title in self.page_titles:
                        if title in line and ' -' not in line:
                            page_index += 1
                            current_page = self.pages[page_index]
                            header_feed = True

                    if current_page.url != 'home':
                        term = re.search("<strong>(.*)</strong>", line)
                        if term is not None:
                            vocab_word = Term(term.group(1))
                            current_page.main_text += f'<a name="{vocab_word.long}"></a>'
                            if vocab_word.long not in self.page_titles:
                                current_page.vocab.append(vocab_word)

                if header_feed:
                    current_page.header_text += line
                else:
                    current_page.main_text += line

    def insert_external_links(self):
        external_links = {
            'Greco': 'https://en.wikipedia.org/wiki/Greece',
            'Mediterranean Sea': 'https://en.wikipedia.org/wiki/Mediterranean_Sea',
            'Colonialism': 'https://en.wikipedia.org/wiki/Colonialism',
            'Steampunk': 'https://en.wikipedia.org/wiki/Steampunk',
            'Humanoid': 'https://www.5esrd.com/gamemastering/monsters-foes/monsters-by-type/humanoids',
            'Hawaii': 'https://en.wikipedia.org/wiki/Hawaii',
            'Eberron': 'https://eberron.fandom.com/wiki/Eberron_Wiki',
            'House Ghallanda': 'https://eberron.fandom.com/wiki/House_Ghallanda',
            'Switzerland': 'https://en.wikipedia.org/wiki/Switzerland'
        }

        for class_name in [
            'Barbarian',
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

        for spell_name in [
            'Guidance',
            'Detect thoughts',
            'Identify']:

            external_links[spell_name] = 'http://dnd5e.wikidot.com/spell:' + '-'.join(spell_name.lower().split())

        for page in self.pages:
            page.maintenance(external_links)

    def build(self):
        self.insert_external_links()
        for page1 in self.pages:
            for page2 in self.pages:
                page1.cross_reference(page2)
            page1.write()


class Term:
    def __init__(self, term):
        self.long = self.pre_clean(term)
        self.short = self.post_clean(self.long)

    def pre_clean(self, term):
        return term.replace(' -', '').replace('<u>', '').replace('</u>', '').rstrip()

    def post_clean(self, term): # add brackets
        return remove_articles(re.sub(r"\([^()]*\)", '', term).rstrip(' ()'))


def remove_articles(term):
    split_term = term.split()
    try:
        if split_term[0] in ['The', 'A', 'An']:
            return ' '.join(split_term[1:])
    except:
        print(term, split_term)
        quit()
    else:
        return term


def download_source():
    import gdown
    import pypandoc

    source = 'https://docs.google.com/document/export?format=docx&id=10zOwNbnFIhr0NnuXhmXsRoRdr_eq7BBZ2lnI3Hb8Gw0'
    gdown.download(source, 'pyrrhos.docx', quiet=True)
    pypandoc.convert_file('pyrrhos.docx', 'html', outputfile="raw.html")


def main():
    download_source()

    website = Website (
        page_titles=[
            'Home Page',
            'A Geographical Overview of Pyrrhos',
            'Political Overview of Pyrrhos',
            'The Races of Pyrrhos',
            'Religion',
            'Monsters',
            'Cosmology'
        ]
    )

    website.pages[0].add_images('world', 'cover')
    website.read_source('raw.html')

    world_map = Page('Map', auto_images=True, img_class='map')
    players = Page('Players', auto_images=True)
    npcs = Page('NPCs', auto_images=True)
    website.pages = website.pages + [world_map, players, npcs]

    for term in website.pages[3].vocab:
        website.pages[3].main_text = website.pages[3].main_text.replace(term.long + ' -', term.long + f' <a href="https://d-n-d5e.fandom.com/wiki/{"_".join(term.short.split(" "))}">[wiki]</a> -')
    for term in website.pages[5].vocab:
        website.pages[5].main_text = website.pages[5].main_text.replace(term.long + ' -', term.long + f' <a href="https://www.5esrd.com/gamemastering/monsters-foes/monsters-by-type/{"_".join(term.short.split(" "))}">[wiki]</a> -')

    website.build()


main()
