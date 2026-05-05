"""
Adds annotations from Hypothes.is data to chapter text in HTML.

Inputs:
    - chapter data CSV file
    - annotation data CSV file
    - raw HTML of chapter text

Output:
    - annotated chapter text in HTML files with YAML front matter for Jekyll site
"""

import csv
import unicodedata

from my_chapters import Chapter

CHAPTER_DATA_FILE = 'data/chapter_data.csv'
ANNOTATION_DATA_FILE = 'data/annotation_data/comments-chapters-00-03.csv'


def main():
    chapters = get_chapters()
    for chapter in chapters:
        chapter_text = chapter.get_clean_html()
        chapter_annotations = chapter.get_annotations(ANNOTATION_DATA_FILE)
        annotated_chapter_text = annotate_one_chapter(chapter_text, chapter_annotations)
        normalized_chapter_text = normalize_chapter_text(annotated_chapter_text)
        write_output_file(chapter, normalized_chapter_text)
        print_report(chapter, chapter_annotations, annotated_chapter_text)


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
    starting_annotation = chapter_annotations[starting_index]
    index_of_next_annotation = starting_index + 1
    next_annotation = chapter_annotations[index_of_next_annotation]
    # check if next annotation is a parent to the first one
    if (next_annotation.start_position <= starting_annotation.start_position
            and next_annotation.end_position >= starting_annotation.end_position):
        next_annotation.children.append(starting_annotation)
        starting_annotation.is_child = True
        identify_parent_and_child_annotations(chapter_annotations, index_of_next_annotation)
    # check if first annotation is a parent to the second one
    elif (next_annotation.start_position >= starting_annotation.start_position
          and next_annotation.end_position <= starting_annotation.end_position):
        starting_annotation.children.append(next_annotation)
        next_annotation.is_child = True
        identify_parent_and_child_annotations(chapter_annotations, index_of_next_annotation)
    return


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


def print_report(chapter, chapter_annotations, annotated_chapter_text):
    """
    Prints a report of the success rate of adding annotations to the chapter.

    Includes:
        - Count of annotations successfully added
        - Percentage of annotations successfully added
        - Report containing id, text, suffix, text_html, suffix_html, and is_child of missed annotations

    Issues identified so far:
        Addressed:
            - Many of the missed annotations are missing leading whitespace on their suffixes, causing replace to fail.
        Unaddressed:
            -
    """
    added_annotations = get_added_annotations(chapter_annotations, annotated_chapter_text)
    missed_annotations = get_missed_annotations(chapter_annotations, annotated_chapter_text)

    print('----------------------------------------------------')
    print()
    print(
        f'{added_annotations} annotations out of {len(chapter_annotations)} added to chapter {chapter.number} {chapter.language}.')
    print(
        f'Percentage of annotations successfully added: {added_annotations / len(chapter_annotations) * 100:.2f}%')
    print()
    # if len(missed_annotations) > 0:
    #     print(f'{"Annotations missed in " + chapter.number + " " + chapter.language:^140}')
    #     print()
    #     print(f'{'id':<30}{'text':<40}{'suffix':<10}{'text_html':<40}{'suffix_html':<10}{'is_child':>20}')
    #
    #     for annotation in missed_annotations:
    #         print(f'{annotation.id:<30}'
    #               f'{"'" + annotation.text + "'":<40}'
    #               f'{"'" + annotation.suffix + "'":<10}'
    #               f'{"'" + annotation.text_html + "'":<40}'
    #               f'{"'" + annotation.suffix_html + "'":<10}'
    #               f'{str(annotation.is_child):>20}')
    #     print()


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


if __name__ == '__main__':
    main()
