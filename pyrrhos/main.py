import re


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
        if self != other_page:
            for word in other_page.vocab:
                if word == 'Nardone':
                    continue
                mod_word = re.sub(r"\([^()]*\)", "", word).rstrip(' ()')
                for v in [mod_word, mod_word.lower(), mod_word + 's', mod_word.lower() + 's']:
                    for w in [' ' + v + ' ', ' ' + v + ',', ' ' + v + '.', ' ' + v + '!']:
                        self.main_text = self.main_text.replace(w, w[0] + f'<a href="{other_page.url + ".html"}#{word}">{v}</a>' + w[-1])

    def write(self):
        with open(self.url + '.html', 'w') as f:
            # CSS
            f.write('<link rel="stylesheet" href="style.css">\n')

            # Title
            f.write('<h1>Pyrrhos</h1>\n')

            # Links
            f.writelines(['<h2>'] + [f'<a href="{url + ".html"}">{url.upper()}</a> ' if self.url != url else f'{url.upper()} ' for url in Page.urls] + ['</h2>\n'])

            # Header
            f.writelines(self.header_text)

            # Table of Contents
            if len(self.vocab) > 0:
                f.write('<toc>\n<li><strong>CONTENTS</strong>\n</li>\n')
                f.writelines([f'<li><blockquote>\n<a href="#{word}">{word}</a>\n</li></blockquote>\n' for word in self.vocab])
                f.write('</toc>\n')

            # Body
            f.writelines(self.main_text)


def download_source():
    import gdown
    import pypandoc

    source = 'https://docs.google.com/document/export?format=docx&id=1ytATWxoHUMBGNWV_XeqcI-OS9cWWSE_pKVszt2ZTQuE'
    gdown.download(source, 'pyrrhos.docx', quiet=True)
    pypandoc.convert_file('pyrrhos.docx', 'html', outputfile="raw.html")


def build_website():
    pages, page_index = [], 1
    for page_title in ['Home Page', 'A Geographical Overview of Pyrrhos', 'Political Overview of Pyrrhos', 'The Races of Pyrrhos', 'Religions', 'Monsters', 'Cosmology']:
        pages.append(Page(page_title))

    with open('raw.html', 'r') as f:
        lines = f.readlines()
        current_page = pages[0]

        header_feed = True
        for line in lines:
            if header_feed and ('<strong' in line or '<ol' in line or '<em' in line):
                header_feed = False
            if '<strong>' in line:
                for title in Page.titles:
                    if title in line:
                        current_page = pages[page_index]
                        page_index += 1
                        header_feed = True
                if current_page.url != 'home':
                    term = re.search("<strong>(.*)</strong>", line)
                    if term is not None:
                        term = term.group(1).replace(' -', '').replace('<u>', '').replace('</u>', '').rstrip()
                        current_page.main_text += f'<a name="{term}"></a>'
                        if current_page.url not in ['monsters', 'cosmology'] and term not in Page.titles:
                            current_page.vocab.append(term)

            if header_feed:
                current_page.header_text += line
            else:
                current_page.main_text += line

    world_map = Page('Map of the World')
    world_map.main_text += '<img src="./erebos.png" alt="Map of Erebos">\n<img src="./orestes.png" alt="Map of Orestes">'
    pages.append(world_map)

    for page1 in pages:
        for page2 in pages:
            page1.cross_reference(page2)
        page1.write()


def main():
    # download_source()
    build_website()


main()
