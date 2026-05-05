"""This module contains the Chapter class for Encyclopedia of the Dog."""

from dataclasses import dataclass
from html import unescape


@dataclass
class Chapter:
    number: str
    language: str
    title: str
    author: str
    translator: str = ''

    def get_read_path(self):
        return f'data/raw_html/{self.number}_{self.language}.html'

    def get_write_path(self):
        return f'data/output/{self.number}_{self.language}.html'

    def get_clean_html(self):
        infile_name = self.get_read_path()
        with open(infile_name, 'r', encoding='utf-8') as infile:
            chapter_html = infile.read()
            chapter_text = unescape(chapter_html)
            chapter_text = unescape(chapter_html)
        return chapter_text

    def construct_yaml_frontmatter(self):
        frontmatter = ('---\n'
                       f'chapter-number: "{self.number}"\n'
                       f'title: "{self.title}"\n'
                       f'author: "{self.author}"\n'
                       f'translator: "{self.translator}"\n'
                       f'language: "{self.language}"\n'
                       '---\n'
                       '\n')
        return frontmatter
