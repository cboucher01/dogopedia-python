"""This module contains the Chapter class for Encyclopedia of the Dog."""

from dataclasses import dataclass
import csv
from html import unescape

from my_annotations import Annotation

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

    def get_annotations(self, annotation_file):
        with open(annotation_file, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            chapter_annotations = []
            for line in reader:
                if line['ch_num'] == self.number and line['lang'] == self.language:
                    id = line['Id']
                    text = line['highlighted']
                    suffix = line['suffix'][:5]
                    text_html = line['highlighted_html']
                    suffix_html = line['suffix_html'][:5]
                    start = int(line['position_start'])
                    end = int(line['position_end'])
                    children = []
                    annotation = Annotation(id, text, suffix, text_html, suffix_html, start, end, children)
                    chapter_annotations.append(annotation)
            return chapter_annotations

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
