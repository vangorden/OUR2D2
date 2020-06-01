import csv
import html
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

import chardet

tag_regex = re.compile("<.*?>")  # Matches html and xml tags ex: <i>, </i>, or anything between < and >


class Record:
    def __init__(self, title, id_header=None):
        self.title = title
        self.normalized_title = clean_str(title)
        self.id_header = id_header

    def __eq__(self, other):
        if type(other) is type(self):
            return self.normalized_title == other.normalized_title
        return False

    def __hash__(self):
        return hash(self.normalized_title)


def _get_title_key(data):
    title_columns = ['title', 'Title', 'TI', 'Article Title']
    for title in title_columns:
        if title in data.keys():
            return title


def _get_file_encoding(file_path):
    with open(file_path, "rb") as f:
        return chardet.detect(f.read())["encoding"]


def save_csv(file_path, results):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Title"])
        for record in results:
            writer.writerow([record.title])


def get_csv_titles(file_path):
    try:
        with open(file_path, encoding=_get_file_encoding(file_path)) as csv_file:
            reader = csv.DictReader(csv_file)
            data = {}
            for row in reader:
                for header, value in row.items():
                    try:
                        data[header].append(value)
                    except KeyError:
                        data[header] = [value]

            title_lst = []
            title_key = _get_title_key(data)
            for title in data[title_key]:
                title_lst.append(Record(title, id_header=title_key))
    except:
        print(
            "Error reading csv file, please ensure it is exported from one of the following databases: Embase,",
            "ProQuest, PubMed, Web of Science, or PsychInfo",
            file=sys.stderr)

        return []

    find_duplicates(title_lst)
    for dup in find_duplicates(title_lst):
        print(f"Duplicate Title found: {dup.title}", file=sys.stderr)

    return title_lst


def get_xml_titles(file_path):
    """Reads xml file to extract article titles, creates Record object with title and adds it to list to be returned.
    """
    title_lst = []
    try:
        tree = ET.parse(file_path)
        titles = tree.getroot().findall("./records/record/titles/title")
        for title in titles:
            orig_title = title[0].text
            title_lst.append(Record(orig_title))
    except:
        print("Error reading EndNote xml file, please ensure it is exported from EndNote", file=sys.stderr)
        return []

    find_duplicates(title_lst)
    for dup in find_duplicates(title_lst):
        print(f"Duplicate Title found: {dup.title}", file=sys.stderr)

    return title_lst


def clean_str(dirty_str):
    """Removes punctuation, converts to lowercase, removes html/xml tags, attempts to normalize special characters, and
    removes html entities from passed string"""

    # Normalize special encodings
    dirty_str = (unicodedata.normalize("NFD", dirty_str).encode("ascii", "ignore").decode("utf-8"))

    dirty_str = html.unescape(dirty_str)  # replace html entities
    dirty_str = dirty_str.lower()
    dirty_str = tag_regex.sub("", dirty_str)  # remove xml/html tags

    # remove all punctuation
    cleaned_str = "".join(
        c for c in dirty_str if c not in "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~— –“’”"
    ).lower()

    return cleaned_str


def summary_stats(a_titles, b_titles, selection):
    """Returns a string that summarizes the size of each set operation, and also returns the set of titles
    corresponding to the selected set operation"""
    file_a_set = set(a_titles)
    file_b_set = set(b_titles)

    union = file_a_set.union(file_b_set)
    intersection = file_a_set.intersection(file_b_set)
    sym_difference = file_a_set.symmetric_difference(file_b_set)
    a_minus_b = file_a_set - file_b_set
    b_minus_a = file_b_set - file_a_set

    summary_str = (f"Total titles in A: {len(a_titles)}\n"
                   f"Total titles in B: {len(b_titles)}\n"
                   f"Union A ⋃ B: {len(union)}\n"
                   f"Intersection A ⋂ B: {len(intersection)}\n"
                   f"Symmetric Difference A ∆ B: {len(sym_difference)}\n"
                   f"Difference A - B: {len(a_minus_b)}\n"
                   f"Difference B - A: {len(b_minus_a)}")

    operation = set()
    if selection == "B-A":
        operation = b_minus_a
    elif selection == "A-B":
        operation = a_minus_b
    elif selection == "AUB":
        operation = union
    elif selection == "A^B":
        operation = sym_difference
    elif selection == "A⋂B":
        operation = intersection

    return operation, summary_str


def find_duplicates(records):
    """Finds duplicates and returns a set of them"""
    s = set()
    return {record for record in records if record in s or s.add(record)}


def create_title_lists(*args):
    title_lists = []
    for file_path in args:
        if file_path.endswith(".xml"):
            title_lists.append(get_xml_titles(file_path))
        elif file_path.endswith(".csv"):
            title_lists.append(get_csv_titles(file_path))
        else:
            # The GUI shouldn't let the user open anything but .xml or .csv this is used outside GUI
            print(
                f"Error: {file_path} has wrong file extension, must be .xml or .csv",
                file=sys.stderr,
            )
            exit(1)
    return title_lists
