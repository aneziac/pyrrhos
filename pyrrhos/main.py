import re
import os


class Page:
    titles = []
    urls = []

    def __init__(self, title):
        self.title = title
        Page.titles.append(title)

        self.url = remove_articles(self.title).split()[0].lower()
        if self.url == 'geographical': self.url = 'geography'
        if self.url == 'political': self.url = 'politics'
        Page.urls.append(self.url)

        self.vocab = []
        self.header_text = ""
        self.main_text = ""

    def maintenance(self):
        self.vocab = sorted(self.vocab, key=len)[::-1]
        self.main_text = self.main_text.replace('</ul>', '</ul><p><br /></p>')

    def cross_reference(self, other_page):
        if self == other_page:
            return
        for word in other_page.vocab:
            clean_word = clean_parens(word)
            term_map = {}
            for word2 in self.vocab:
                clean_word2 = clean_parens(word2)
                if clean_word in clean_word2:
                    term_encoding = str(hash(clean_word2))
                    term_map[clean_word2] = term_encoding
                    self.main_text = self.main_text.replace(clean_word2, term_encoding)
            for v in [clean_word,
                      clean_word + 's',
                      clean_word[:-2] + 'an',
                      clean_word + 'ish',
                      clean_word[:-1] + 'ves',
                      clean_word[:-1] + 'ven',
                      clean_word[:-4] + 'ian',
                      clean_word[:-1] + 'ish']:
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
                              ' ' + w + '\n']:

                        self.main_text = self.main_text.replace(x, x[0] + f'<a href="{other_page.url + ".html"}#{word}">{v}</a>' + x[-1])

            for term in term_map:
                self.main_text = self.main_text.replace(term_map[term], term)


    def write(self):
        with open('html/' + self.url + '.html', 'w', encoding='UTF-8') as f:

            # Head
            f.write('<!doctype html>\n<html>\n<head>\n')
            f.write('<link rel="stylesheet" href="../css/header.css">\n<link rel="stylesheet" href="../css/body.css">\n')
            f.write(f'<title>\n\tPyrrhos - {self.url.capitalize()}\n</title>\n')

            # Header
            f.write('</head>\n<body>\n')
            f.write('<h1>\n\tPyrrhos\n</h1>\n<h2>\n\t')

            f.writelines([f'<a href="{url + ".html"}">{url.upper()}</a> ' if self.url != url else f'{url.upper()} ' for url in Page.urls])
            f.write('\n</h2>\n')
            f.writelines(self.header_text)

            # Table of Contents
            if len(self.vocab) > 0:
                f.write('<toc>\n<li><strong>CONTENTS</strong>\n</li>\n')
                if self.main_text.count('<ul') >= 2:
                    table_terms = [self.vocab[0]]
                    for term in re.findall("</ul>(.*?)<ul>", self.main_text.replace('\n', '')):
                        table_terms.append(re.search("<strong>(.*)</strong>", term).group(1))
                else:
                    table_terms = self.vocab
                f.writelines([f'<li><blockquote>\n<a href="#{word}">{word}</a>\n</blockquote></li>\n' for word in table_terms])
                f.write('</toc>\n')

            # Main text
            f.writelines(self.main_text)

            # End
            f.write('</body>\n</html>\n')

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


def clean_parens(term): # add brackets
    return remove_articles(re.sub(r"\([^()]*\)", "", term).rstrip(' ()'))


def remove_articles(term):
    term = term.split()
    if term[0] in ['The', 'A', 'An']:
        return ' '.join(term[1:])
    else:
        return ' '.join(term[0:])


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
                        term = clean_term(term.group(1))
                        current_page.main_text += f'<a name="{term}"></a>'
                        if term not in Page.titles:
                            current_page.vocab.append(term)

            if header_feed:
                current_page.header_text += line
            else:
                current_page.main_text += line

    world_map = Page('Map')
    world_map.add_images('map', 'map')

    players = Page('Players')
    players.add_images('players')

    npcs = Page('NPCs')
    npcs.add_images('npcs')

    pages = pages + [world_map, players, npcs]

    for page in pages:
        page.maintenance()

    for page1 in pages:
        for page2 in pages:
            page1.cross_reference(page2)
        page1.write()


def main():
    # download_source()
    build_website()


main()
