import re
import os
from bs4 import BeautifulSoup as bs
import json
from unidecode import unidecode


class Page:
    def __init__(self, title, auto_images=False, img_class='character', source=''):
        self.title = title
        self.source = source

        self.url = remove_articles(self.title).split()[0].lower()
        if self.url == 'geographical':
            self.url = 'geography'
        if self.url == 'political':
            self.url = 'politics'
        if self.url == 'wanderer’s':
            self.url = 'items'
        self.full_url = self.url + '.html'
        self.tab = self.url.capitalize()
        if self.url == 'npcs':
            self.tab = 'NPCs'

        self.navigation_bar = []
        self.vocab = []
        self.header_text = ""
        self.main_text = ""

        if auto_images:
            self.add_images(self.title.lower(), img_class=img_class)

    def maintenance(self):
        self.main_text = self.main_text.replace('</ul>', '</ul><p><br /></p>')
        self.main_text = self.main_text.replace('<em>', '@')
        self.main_text = self.main_text.replace('</em>', '$')

        for term in self.vocab:
            term.link = f'{self.full_url}#{term.long}'
            Website.vocab.append(term)

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

            self.add_links(word)

        for term in term_map:
            self.main_text = self.main_text.replace(term_map[term], term)

    def write(self):
        self.main_text = self.main_text.replace('@', '<em>')
        self.main_text = self.main_text.replace('$', '</em>')

        src = HTML_String()

        # Head
        src.write(f'<title>Pyrrhos - {self.tab}</title>')
        src.write('<meta charset="UTF-8">')

        # Title
        src.write('</head><body><div id="rectangle">')
        src.write('<img alt="pic" class="logo" src="../images/logo/pyrrhos_logo.png"/>')

        # Search bar
        src.write('<input id="searchbar" type="text" placeholder="Search" onfocus=this.value="">')
        src.write('<script src="../js/search.js"></script><h1>')

        # Navigation bar
        src.write_list(self.navigation_bar)
        src.write('</h1></div><div id="line"></div>')

        # Header text
        src.write('<div class="main"><a name="top"></a>')
        src.write(self.header_text)

        # Table of Contents
        if len(self.vocab) > 0:
            src.write('<toc class="header"><strong>Contents</strong></toc><toc><ol>')
            if self.url == 'religion':
                toc_terms = [self.vocab[0]]
                for term in re.findall("</ul>(.*?)<ul>", self.main_text.replace('\n', '')):
                    toc_terms.append(Term(re.search("<strong>(.*)</strong>", term).group(1)))
            else:
                toc_terms = self.vocab

            for term in toc_terms:
                src.write('<li class="toc"><blockquote>')
                src.write(f'<a href="#{term.long}">{term.long}</a>')
                src.write('</blockquote></li>')

            src.write('</ol></toc>')

        # Main text
        src.write(self.main_text)

        # Footer
        src.write('</div><ftr>')
        src.write('<p><a href="#top">Back to top</a></p>')
        src.write(f'<p><a href="{self.source}">Source code</a></p>')
        src.write('</ftr>')

        src.finish()

        with open('html/' + self.full_url, 'w', encoding='UTF-8') as f:
            f.write(src.prettify())

    def add_images(self, image_folder, img_class='character'):
        file_path = './images/' + image_folder
        files = sorted(os.listdir(file_path))
        images = [f for f in files if (f.endswith('.png') or f.endswith('.jpg'))]
        descriptions = [f for f in files if f.endswith('.txt')]

        for source in images:
            self.main_text += f'<img class="{img_class}" src=".{file_path}/{source}" alt="pic">'
            desc = os.path.splitext(source)[0] + '.txt'
            if desc in descriptions:
                with open(file_path + '/' + desc) as f:
                    self.main_text += f'<cap>{f.readlines()[0]}</cap>'

    def add_links(self, term):
        for v in [
            term.short,
            term.short + 's',
            term.short + 'n',
            term.short[:-2] + 'an',
            term.short[:-2] + 'ans',
            term.short + 'ish',
            term.short[:-1] + 'ves',
            term.short[:-1] + 'ven',
            term.short[:-4] + 'ian',
            term.short[:-1] + 'ish',
        ]:

            for w in [v, v.lower()]:
                for x in [
                    ' ' + w + ' ',
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
                    '@' + w + '$',
                    ' ' + w + '\n',
                    ' ' + w + '’',
                ]:

                    replacement = x[0] + f'<a href="{term.link}">{w}</a>' + x[-1]
                    self.header_text = self.header_text.replace(x, replacement)
                    self.main_text = self.main_text.replace(x, replacement)

    def add_wiki(self, base_link, separator="_"):
        for term in self.vocab:
            link = f'{base_link}/{separator.join(remove_parens(term.long).split(" "))}'
            replacement = term.long + f' <a href="{link}">[wiki]</a> -'
            self.main_text = self.main_text.replace(term.long + ' -', replacement)


class HTML_String:
    def __init__(self):
        self.raw_string = "<!DOCTYPE html><html><head>"
        self.raw_string += (
            '<link rel="stylesheet" href="../css/header.css">'
            '<link rel="stylesheet" href="../css/body.css">'
        )

    def write(self, s):
        self.raw_string += s

    def write_list(self, lst):
        self.raw_string += ''.join(lst)

    def finish(self):
        self.write('</body></html>\n')
        self.sub_tags()

    # By default, prettify starts a newline for all tags, which messes up links and formatting
    # To solve, some tags are substituted for hashes, then prettify is executed
    # And then the hashes are substituted back into tags
    # Somehow the < and > characters are getting converted to '&gt;' and '&lt;'
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

    def __init__(self, page_titles=[], source=''):
        self.pages, self.page_titles, self.page_index = [], page_titles, 0
        self.source = source
        for page_title in self.page_titles:
            self.pages.append(Page(page_title, source=source))

    def read_source(self, source_file):
        with open('src_files/' + source_file, 'r') as f:
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
                            remove_s = False
                            if current_page.url == 'monsters':
                                remove_s = True
                            vocab_word = Term(term.group(1), remove_s)
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
            'House Jorasco': 'https://eberron.fandom.com/wiki/House_Jorasco',
            'Roll20': 'https://app.roll20.net/campaigns/details/8231914/pyrrhos-campaign',
            'Spell List': 'http://dnd5e.wikidot.com/spells',
            'Quick Reference': 'https://orbitalbliss.github.io/dnd5e-quickref/quickref.html',
            'Main Pyrrhos Doc': 'https://docs.google.com/document/d/'
            '1ytATWxoHUMBGNWV_XeqcI-OS9cWWSE_pKVszt2ZTQuE/edit',
            'Wanderer\'s Wares Doc': 'https://docs.google.com/document/d/'
            '1TIymiw1LBDr3Y7b0onjNtnRkYOa5JUWyerbfuTLKzec/edit',
            'List of Beasts': 'https://dnd-wiki.org/wiki/5e_Beast_List',
        }

        for class_name in [
            'Barbarian',
            'Bard',
            'Cleric',
            'Druid',
            # 'Fighter',
            'Monk',
            'Paladin',
            'Ranger',
            'Rogue',
            'Sorcerer',
            'Warlock',
            'Wizard',
            'Artificer',
        ]:

            external_links[class_name] = 'https://www.dndbeyond.com/classes/' + class_name.lower()

        for spell_name in [
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
            'identify',
            'zephyr strike',
            'dispel magic',
            'locate object',
            'locate creature',
            'remove curse',
            'produce flame',
            'create bonfire',
        ]:
            spell = '-'.join(spell_name.lower().split())
            external_links[spell_name] = 'http://dnd5e.wikidot.com/spell:' + spell

        for page in self.pages:
            page.maintenance()
            for word in external_links:
                term = Term(word)
                term.link = external_links[word]
                page.add_links(term)

    def write_js(self):
        code = []
        with open('js/search.js', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line == ']\n':
                    code = lines[i + 1 :]
                    break
        with open('js/search.js', 'w') as f:
            f.write("var searchTerms = [\n\t")
            for i, term in enumerate(Website.vocab):
                f.write("`")
                f.write(json.dumps(term.__dict__))
                if i < len(Website.vocab) - 1:
                    f.write("`,\n\t")
                else:
                    f.write("`\n")
            f.write("]\n")
            f.writelines(code)

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
    def __init__(self, term, remove_s=False):
        self.long = self.get_long(term)
        self.short = self.get_short(self.long, remove_s)

    def get_long(self, term):
        return term.replace(' -', '').replace('<u>', '').replace('</u>', '').rstrip()

    def get_short(self, term, remove_s):
        if remove_s and term[-1] == 's':
            term = term[:-1]
        if 'the' in term:
            term = term.split(' the')[0]
        return unidecode(remove_articles(remove_parens(term)))


def remove_parens(term):
    return re.sub(r'\[.*?\]', '', re.sub(r'\([^()|\[\]]*\)', '', term)).rstrip()


def remove_articles(term):
    split_term = term.split()
    if split_term[0] in ['The', 'A', 'An']:
        return ' '.join(split_term[1:])
    else:
        return term


def download_source(download_fresh=False):
    def doc_to_html(doc_id, name):
        url = 'https://docs.google.com/document/export?format=docx&id=' + doc_id
        raw_doc = 'src_files/' + name + '.docx'
        raw_html = 'src_files/' + name + '.html'
        gdown.download(url, raw_doc, quiet=True)
        pypandoc.convert_file(raw_doc, 'html', outputfile=raw_html)

    if 'src_files' not in os.listdir('.'):
        os.makedirs('src_files')
        download_fresh = True

    if download_fresh:
        import gdown
        import pypandoc

        doc_to_html('10zOwNbnFIhr0NnuXhmXsRoRdr_eq7BBZ2lnI3Hb8Gw0', 'pyrrhos')
        doc_to_html('1chN4NrMKjeri804bMwmTY-Cn7i7RVJ7z9voxhNNwZ10', 'wanderer')


def main():
    download_source()

    website = Website(
        page_titles=[
            'Home Page',
            'A Geographical Overview of Pyrrhos',
            'Political Overview of Pyrrhos',
            'The Races of Pyrrhos',
            'Religion',
            'Monsters',
            'Demons',
            'Cosmology',
            'The Wanderer’s Wares',
        ],
        source='https://github.com/aneziac/pyrrhos',
    )

    website.pages[0].add_images('world', 'cover')
    website.read_source('pyrrhos.html')
    website.read_source('wanderer.html')

    world_map = Page('Map', auto_images=True, img_class='map')
    players = Page('Players', auto_images=True)
    npcs = Page('NPCs', auto_images=True)

    links = Page('Links')
    links.main_text += '<p><strong><u>List of Useful Links</u></strong></p><p> '
    links.main_text += ' </p><p> '.join(
        [
            'Roll20',
            'Spell List',
            'Quick Reference',
            'Main Pyrrhos Doc',
            'Wanderer\'s Wares Doc',
            'List of Beasts',
        ]
    )
    links.main_text += ' </p>'

    website.pages = website.pages + [world_map, players, npcs, links]

    website.pages[3].add_wiki('https://d-n-d5e.fandom.com/wiki')
    website.pages[5].add_wiki('https://www.5esrd.com/gamemastering/monsters-foes/monsters-by-type')

    website.build()


main()
