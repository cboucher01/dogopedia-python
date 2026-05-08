"""
Adds annotations from Hypothes.is data to chapter text in HTML.

Inputs:
    - chapter data CSV file
    - annotation data CSV file
    - raw HTML of chapter text

Output:
    - annotated chapter text in HTML files with YAML front matter for Jekyll site
    - reports of missed annotations for each chapter
"""

import csv
import unicodedata
import os

from my_chapters import Chapter
from my_annotations import Annotation

CHAPTER_DATA_FILE = 'data/chapter_data.csv'
ANNOTATION_DATA_FILE = 'data/annotation_data/comments-all.csv'


def main():
    chapters = get_chapters()
    for chapter in chapters:
        chapter_text = chapter.get_clean_html()
        chapter_annotations = get_annotations(chapter, ANNOTATION_DATA_FILE)
        annotated_chapter_text = annotate_one_chapter(chapter_text, chapter_annotations)
        normalized_chapter_text = normalize_chapter_text(annotated_chapter_text)
        write_output_file(chapter, normalized_chapter_text)
        write_reports(chapter, chapter_annotations, annotated_chapter_text)


def get_chapters():
    with open(CHAPTER_DATA_FILE, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        chapters = []
        for row in reader:
            number = row["number"]
            language = row["language"]
            title = row["title"]
            author = row["author"]
            translator = row["translator"]
            chapter = Chapter(number, language, title, author, translator)
            chapters.append(chapter)
    return chapters


def get_annotations(chapter, annotation_file):
    with open(annotation_file, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        chapter_annotations = []
        for line in reader:
            if line['ch_num'] == chapter.number and line['lang'] == chapter.language:
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


def annotate_one_chapter(chapter_text, chapter_annotations):
    identify_parent_and_child_annotations(chapter_annotations)
    for i in range(len(chapter_annotations)):
        annotation = chapter_annotations[i]
        annotation.unescape_text()
        if not annotation.is_child:
            try:
                chapter_text = add_annotation(annotation, chapter_text)
            except ValueError:
                # improves chapter 01 en success rate from 79.76% to 91.76%
                chapter_text = add_annotation_with_missing_space(annotation, chapter_text)
    return chapter_text


def identify_parent_and_child_annotations(chapter_annotations, starting_index=0):
    """
    Updates Annotation objects in chapter_annotations with data about parent and child annotations.

    Iterates through chapter_annotations and checks start and end position in relation to those of the next annotation.
    """
    starting_index = starting_index
    index_of_next_annotation = starting_index + 1
    for i in range(starting_index, len(chapter_annotations) - 1):
        starting_annotation = chapter_annotations[starting_index]
        next_annotation = chapter_annotations[index_of_next_annotation]
        # check if next annotation is a parent to the first one
        if (next_annotation.start_position <= starting_annotation.start_position
                and next_annotation.end_position >= starting_annotation.end_position):
            next_annotation.children.append(starting_annotation)
            starting_annotation.is_child = True
        # check if first annotation is a parent to the second one
        elif (next_annotation.start_position >= starting_annotation.start_position
                and next_annotation.end_position <= starting_annotation.end_position):
            starting_annotation.children.append(next_annotation)
            next_annotation.is_child = True
        starting_index += 1
        index_of_next_annotation += 1


def add_annotation(annotation, chapter_text):
    chapter_text.index(annotation.text_with_suffix())
    chapter_text = chapter_text.replace(annotation.text_with_suffix(),
                                        annotation.text_with_markup_and_suffix())
    return chapter_text


def add_annotation_with_missing_space(annotation, chapter_text):
    try:
        # try adding a space to the beginning of the suffix
        annotation.suffix_html = f'{" " + annotation.suffix_html}'
        chapter_text = add_annotation(annotation, chapter_text)
    except ValueError:
        # if it does not work, take the added space away
        annotation.suffix_html = annotation.suffix_html[1:]
    return chapter_text


def normalize_chapter_text(annotated_chapter_text):
    normalized_chapter_text = unicodedata.normalize('NFKD', annotated_chapter_text)
    return normalized_chapter_text


def write_output_file(chapter, normalized_chapter_text):
    normalized_chapter_text_with_frontmatter = f'{chapter.construct_yaml_frontmatter() + normalized_chapter_text}'
    outfile_name = chapter.get_write_path()
    with open(outfile_name, "w") as outfile:
        outfile.write(normalized_chapter_text_with_frontmatter)


def write_reports(chapter, chapter_annotations, annotated_chapter_text):
    """
    Prints a report of the success rate of adding annotations to the chapter, then writes a CSV report
    of missed annotations.

    Includes:
        - Count of annotations successfully added
        - Percentage of annotations successfully added
        - Report containing metadata for missed annotations

    Issues identified so far:
        Addressed:
            - Many of the missed annotations are missing leading whitespace on their suffixes, causing replace to fail.
        Unaddressed:
            - None, currently
    """
    added_annotations = get_added_annotations(chapter_annotations, annotated_chapter_text)
    missed_annotations = get_missed_annotations(chapter_annotations, annotated_chapter_text)

    print('-----------------------------------------------------')
    print(f'{'Chapter ' + chapter.number + '_' + chapter.language:^53}\n')
    print_success_rate_report(added_annotations, chapter_annotations)

    outfile_name = chapter.get_missed_annotations_report_path()
    delete_old_report(outfile_name)
    write_missed_annotations_report(missed_annotations, outfile_name)


def get_added_annotations(chapter_annotations, clean_chapter_text):
    added_annotations = 0
    for annotation in chapter_annotations:
        if annotation.id in clean_chapter_text:
            added_annotations += 1
    return added_annotations


def get_missed_annotations(chapter_annotations, clean_chapter_text):
    missed_annotations = []
    for annotation in chapter_annotations:
        if annotation.id not in clean_chapter_text:
            missed_annotations.append(annotation)
    return missed_annotations


def print_success_rate_report(added_annotations, chapter_annotations):
    print(
        f'Added {added_annotations} annotations out of {len(chapter_annotations)}.')
    print(
        f'Percentage of annotations successfully added: {added_annotations / len(chapter_annotations) * 100:.2f}%')


def delete_old_report(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def write_missed_annotations_report(missed_annotations, outfile_name):
    if len(missed_annotations) > 0:
        with open(outfile_name, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['id', 'text', 'suffix', 'text_html', 'suffix_html', 'start_position',
                             'end_position', 'children', 'is_child'])
            for annotation in missed_annotations:
                writer.writerow([annotation.id, annotation.text, annotation.suffix, annotation.text_html,
                                 annotation.suffix_html, annotation.start_position, annotation.end_position,
                                 annotation.children, annotation.is_child])


if __name__ == '__main__':
    main()
