import re
import os
from bs4 import BeautifulSoup as bs
import json


class Page:
    def __init__(self, title, auto_images=False, img_class='character'):
        self.title = title

        self.url = remove_articles(self.title).split()[0].lower()
        if self.url == 'geographical': self.url = 'geography'
        if self.url == 'political': self.url = 'politics'
        if self.url == 'wanderer\'s': self.url = 'items'
        self.full_url = self.url + '.html'
        self.tab = self.url.capitalize()
        if self.url == 'npcs': self.tab = 'NPCs'

        self.navigation_bar = []
        self.vocab = []
        self.header_text = ""
        self.main_text = ""

        if auto_images:
            self.add_images(self.title.lower(), img_class=img_class)

    def maintenance(self, external_links):
        self.main_text = self.main_text.replace('</ul>', '</ul><p><br /></p>')

        for term in self.vocab:
            term.link = f'{self.full_url}#{term.long}'
            Website.vocab.append(term)

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

        # Header
        src.write('</head><body><div id="rectangle"><a name="top"></a>')
        src.write('<h1>Pyrrhos</h1><input id="searchbar" onkeyup="search()" type="text"  placeholder="Search">')
        src.write('<script src="../js/search_gen.js"></script><h2>')

        src.write_list(self.navigation_bar)
        src.write('</h2></div><div class="main">')
        src.write(self.header_text)

        # Table of Contents
        if len(self.vocab) > 0:
            src.write('<toc class="header"><strong>Contents</strong></toc><toc>')
            if self.url == 'religion': # self.main_text.count('<ul') >= 2:
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
                substring.short[:-2] + 'ans',
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
                        '>' + w + '<',
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
        self.sub_tags()

    # By default, prettify starts a newline for anchors, which messes up all links
    # To solve, links are substituted for hashes, then prettify is executed, then the hashes are substituted back into links
    # Somehow the > character after the link is getting converted to '&gt;'
    # To do: investigate this issue

    def sub_tags(self):
        self.raw_string = self.raw_string.replace('<a', str(hash('<a')))
        self.raw_string = self.raw_string.replace('</a>', str(hash('</a>')))
        self.raw_string = self.raw_string.replace('<em', str(hash('<em')))
        self.raw_string = self.raw_string.replace('</em>', str(hash('</em>')))

    def resub_tags(self, string):
        string = string.replace(str(hash('<a')), '<a')
        string = string.replace(str(hash('</a>')), '</a>')
        string = string.replace(str(hash('<em')), '<em')
        string = string.replace(str(hash('</em>')), '</em>')
        string = string.replace('&gt;', '>')  # what is causing this?
        string = string.replace('&lt;', '<')  # what is causing this?
        return string

    def prettify(self):
        soup = bs(self.raw_string, features="html.parser")
        return self.resub_tags(soup.prettify())


class Website:
    vocab = []

    def __init__(self, page_titles=[]):
        self.pages, self.page_titles, self.page_index = [], page_titles, 0
        for page_title in self.page_titles:
            self.pages.append(Page(page_title))

    def read_source(self, source_file):
        with open(source_file, 'r') as f:
            lines = f.readlines()
            current_page = self.pages[self.page_index]

            header_feed = True
            for line in lines:
                line = line.replace('e`', 'è')
                if header_feed and True in [t in line for t in ['<strong', '<ol', '<em', '<ul']]:
                    header_feed = False

                if '<strong>' in line:
                    for title in self.page_titles:
                        if title in line and ' -' not in line:
                            self.page_index += 1
                            current_page = self.pages[self.page_index]
                            header_feed = True

                    if current_page.url != 'home':
                        term = re.search("<strong>(.*)</strong>", line)
                        if term is not None:
                            vocab_word = Term(term.group(1).replace('è', 'e'))
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
            'Eldeen Reaches': 'https://eberron.fandom.com/wiki/Eldeen_Reaches',
            'House Cannith': 'https://eberron.fandom.com/wiki/House_Cannith',
            'House Jorasco': 'https://eberron.fandom.com/wiki/House_Jorasco'
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
            # 'Guidance',
            'Detect thoughts',
            'Identify',
            'True Resurrection',
            'Power Word Heal',
            'Regeneration',
            'Find Familiar',
            'Flock of Familiars',
            'shape water',
            'druidcraft',
            'prestidigitation',
            'wall of force',
            'inflict wounds',
            'speak with dead',
            'animate dead',
            'blight',
            'wristpocket',
            'dispel magic',
            'mental prison',
            'disintegrate',
            'greater restoration',
            'wish',
            'identify',
            'zephyr strike',
            'dispel magic',
            'locate object',
            'locate creature',
            'remove curse',
            'command'
            ]:

            external_links[spell_name] = 'http://dnd5e.wikidot.com/spell:' + '-'.join(spell_name.lower().split())

        for page in self.pages:
            page.maintenance(external_links)

    def write_js(self):
        with open('js/search_gen.js', 'w') as f:
            with open('js/search_src.js', 'r') as g:
                f.writelines(g.readlines())
            f.write("\nvar data = [\n\t")
            for i, term in enumerate(Website.vocab):
                f.write("'")
                f.write(json.dumps(term.__dict__))
                if i < len(Website.vocab) - 1:
                    f.write("',\n\t")
                else:
                    f.write("'\n")
            f.write("]\n")

    def navigation(self):
        for page1 in self.pages:
            for page2 in self.pages:
                if page1 == page2:
                    page1.navigation_bar.append(page1.tab + ' ')
                else:
                    page1.navigation_bar.append(f'<a href="{page2.url + ".html"}">{page2.tab}</a> ')

    def build(self):
        self.insert_external_links()
        self.write_js()
        self.navigation()
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
    if split_term[0] in ['The', 'A', 'An']:
        return ' '.join(split_term[1:])
    else:
        return term


def download_source():
    import gdown
    import pypandoc

    def doc_to_html(doc_id, name):
        source = 'https://docs.google.com/document/export?format=docx&id=' + doc_id
        gdown.download(source, name + '.docx', quiet=True)
        pypandoc.convert_file(name + '.docx', 'html', outputfile=name + '.html')

    doc_to_html('10zOwNbnFIhr0NnuXhmXsRoRdr_eq7BBZ2lnI3Hb8Gw0', 'pyrrhos')
    # doc_to_html('1TIymiw1LBDr3Y7b0onjNtnRkYOa5JUWyerbfuTLKzec', 'wanderer')


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
            'Cosmology',
            'The Wanderer\'s Wares'
        ]
    )

    website.pages[0].add_images('world', 'cover')
    website.read_source('pyrrhos.html')
    website.read_source('wanderer.html')

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
