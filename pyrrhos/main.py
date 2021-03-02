import re
import os


class Page:
    titles = []
    urls = []

    def __init__(self, title):
        self.title = title
        Page.titles.append(title)

        self.url = self.title.split()[:2]
        if self.url[0] in ['The', 'A', 'An']:
            self.url = self.url[1].lower()
        else:
            self.url = self.url[0].lower()
        if self.url == 'geographical': self.url = 'geography'
        if self.url == 'political': self.url = 'politics'
        Page.urls.append(self.url)

        self.vocab = []
        self.header_text = ""
        self.main_text = ""

    def cross_reference(self, other_page):
        if self == other_page:
            return
        for word in other_page.vocab:
            clean_word = clean_parens(word)
            if True in [clean_word in clean_parens(word2) for word2 in self.vocab]:
                continue

            for v in [clean_word, clean_word + 's', clean_word[:-2] + 'an', clean_word + 'ish', clean_word[-1] + 'ves']:
                for w in [v, v.lower()]:
                    for x in [' ' + w + ' ', ' ' + w + ',', ' ' + w + '.', ' ' + w + '!', ' ' + w + ')', ' ' + w + "’", ' ' + w + '?']:
                        self.main_text = self.main_text.replace(x, x[0] + f'<a href="{other_page.url + ".html"}#{word}">{v}</a>' + x[-1])

    def write(self):
        with open('html/' + self.url + '.html', 'w') as f:

            # Head
            f.write('<!doctype html>\n<html>\n<head>\n')
            f.write('<link rel="stylesheet" href="../css/header.css">\n<link rel="stylesheet" href="../css/body.css">\n')
            f.write(f'<title>\n\tPyrrhos - {self.url.capitalize()}\n</title>\n')

            # Header
            f.write('</head>\n<body>\n')
            f.write('<h1>\n\tPyrrhos\n</h1>\n')
            f.writelines(['<h2>\n\t'] + [f'<a href="{url + ".html"}">{url.upper()}</a> ' if self.url != url else f'{url.upper()} ' for url in Page.urls] + ['\n</h2>\n'])
            f.writelines(self.header_text)

            # Table of Contents
            if len(self.vocab) > 0:
                f.write('<toc>\n<li><strong>CONTENTS</strong>\n</li>\n')
                f.writelines([f'<li><blockquote>\n<a href="#{word}">{word}</a>\n</blockquote></li>\n' for word in self.vocab])
                f.write('</toc>\n')

            # Main text
            f.writelines(self.main_text)

            f.write('</body>\n</html>')

    def add_images(self, image_folder, img_class='character'):
        file_path = './images/' + image_folder
        images = [f for f in sorted(os.listdir(file_path)) if (f.endswith('.png') or f.endswith('.jpg'))]
        descriptions = [f for f in os.listdir(file_path) if f.endswith('.txt')]
        for source in images:
            self.main_text += f'<img class="{img_class}" src=".{file_path}/{source}" alt="picture here">\n'
            desc = os.path.splitext(source)[0] + '.txt'
            if desc in descriptions:
                with open(file_path + '/' + desc) as f:
                    self.main_text += f'<cap>\n\t{f.readlines()[0]}</cap>\n'

def download_source():
    import gdown
    import pypandoc

    source = 'https://docs.google.com/document/export?format=docx&id=10zOwNbnFIhr0NnuXhmXsRoRdr_eq7BBZ2lnI3Hb8Gw0'
    gdown.download(source, 'pyrrhos.docx', quiet=True)
    pypandoc.convert_file('pyrrhos.docx', 'html', outputfile="raw.html")


def clean_term(term):
    return term.replace(' -', '').replace('<u>', '').replace('</u>', '').rstrip()


def clean_parens(term):
    return re.sub(r"\([^()]*\)", "", term).rstrip(' ()')


def build_website():
    pages, page_index = [], 1
    for page_title in ['Home Page',
                       'A Geographical Overview of Pyrrhos',
                       'Political Overview of Pyrrhos',
                       'The Races of Pyrrhos',
                       'Religions',
                       'Monsters',
                       'Cosmology']:
        pages.append(Page(page_title))

    pages[0].add_images('world', 'cover')

    with open('raw.html', 'r') as f:
        lines = f.readlines()
        current_page = pages[0]

        header_feed = True
        for line in lines:
            if header_feed and True in [t in line for t in ['<strong', '<ol', '<em', 'ul']]:
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
                        term = clean_term(term.group(1))
                        current_page.main_text += f'<a name="{term}"></a>'
                        if term not in Page.titles:
                            current_page.vocab.append(term)

            if header_feed:
                current_page.header_text += line
            else:
                current_page.main_text += line

    world_map = Page('Map of the World')
    world_map.add_images('map', 'map')
    world_map.write()

    players = Page('Players of Campaign')
    players.add_images('players')
    players.write()

    npcs = Page('NPCs of the World')
    npcs.add_images('npcs')
    npcs.write()

    pages = pages + [world_map, players, npcs]

    for page1 in pages:
        for page2 in pages:
            page1.cross_reference(page2)
        page1.write()

def main():
    # download_source()
    build_website()


main()
