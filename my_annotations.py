"""This module contains the Annotation class for Encyclopedia of the Dog."""

from dataclasses import dataclass
from html import unescape


@dataclass
class Annotation:
    id: str
    text: str
    suffix: str
    text_html: str
    suffix_html: str
    start_position: int
    end_position: int
    children: list
    is_child: bool = False

    def unescape_text(self):
        self.text_html = unescape(self.text_html)

    def add_child_annotations_to_text(self):
        text_with_child_annotations = self.text_html
        for child in self.children:
            if text_with_child_annotations.find(child.text_html) != -1:
                text_with_child_annotations = text_with_child_annotations.replace(child.text_html,
                                                                                  child.text_with_markup())
        return text_with_child_annotations

    def text_with_suffix(self):
        """
        Appends the suffix to the end of the text of the annotation.

        Returns:
            (str) text_with_suffix
        """
        return f'{self.text_html}{self.suffix_html}'

    def text_with_markup(self):
        """
        Adds HTML markup to the text of the annotation.

        Returns:
            (str) text_with_markup
        """
        return f'<span id="highlight-{self.id}" class="annotation-link" role="link" onclick="window.location.href=\'#{self.id}\';" tabindex="-1" aria-hidden="true">{self.add_child_annotations_to_text()}</span>'

    def text_with_markup_and_suffix(self):
        """
        Adds HTML markup to the text and appends the suffix to the end.

        Returns:
            (str) text_with_markup_and_suffix
        """
        return f'<span id="highlight-{self.id}" class="annotation-link" role="link" onclick="window.location.href=\'#{self.id}\';" tabindex="-1" aria-hidden="true">{self.add_child_annotations_to_text()}</span>{self.suffix_html}'


"""
todo:
 - figure out how to handle annotations that partially overlap (not parents and children)
 - add some 'try' or other conditional thing to handle common errors in the data

common errors:
 - some suffixes are missing their leading whitespace, causing text_with_suffix() to not be found and replaced
"""