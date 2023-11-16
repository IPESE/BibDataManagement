from pathlib import Path
import sys
from csv import Sniffer
import os
import os.path as op
import pandas as pd
import re
import importlib.resources
import string

def file_reader(file):
    """To read data files correctly, whether there are csv, txt, dat or excel"""
    file = Path(file)
    try:
        if file.suffix == '.csv' or file.suffix == '.dat' or file.suffix == '.txt':
            sniffer = Sniffer()
            with open(file, 'r') as f:
                line = next(f).strip()
                delim = sniffer.sniff(line)
            return pd.read_csv(file, sep=delim.delimiter)
        elif file.suffix == '.xlsx':
            return pd.read_excel(file)
        else:
            return pd.read_table(file)
    except:
        print('It seems there is a problem while reading the file...\n')
        print("%s" % sys.exc_info()[1])


def find_file(path):
    if op.isfile(path):
        return path
    elif op.isfile(op.abspath(path)):
        return path
    else:
        raise ValueError("The file was not found under the name given.")


def md_table(listOfDicts):
    """Loop through a list of dicts and return a markdown table as a multi-line string.

    listOfDicts -- A list of dictionaries, each dict is a row
    """
    markdowntable = ""
    # Make a string of all the keys in the first dict with pipes before after and between each key
    markdownheader = '| ' + ' | '.join(map(str, listOfDicts[0].keys())) + ' |'
    # Make a header separator line with dashes instead of key names
    markdownheaderseparator = '|-----' * len(listOfDicts[0].keys()) + '|'
    # Add the header row and separator to the table
    markdowntable += markdownheader + '\n'
    markdowntable += markdownheaderseparator + '\n'
    # Loop through the list of dictionaries outputting the rows
    for row in listOfDicts:
        markdownrow = ""
        for key, col in row.items():
            markdownrow += '| ' + str(col) + ' '
        markdowntable += markdownrow + '|' + '\n'
    return markdowntable


def keep_reference_df(df):
    def fill_column_with_reference(row):
        for col in row.index.tolist():
            if re.search('_x', col) is not None:
                if row[col] is None:
                    row[col.replace('_x', '')] = row[col.replace('_x', '_y')]
                else:
                    row[col.replace('_x', '')] = row[col]
        return row
    df = df.apply(fill_column_with_reference, axis=1)
    df = df.drop(df.filter(regex='_y$|_x$').columns, axis=1)

    return df


def get_file(path_to_find, path_to_save):
    """
    Get the non-python files from package and save them to filepath

    Parameters:
    ----------
    - path_to_find: the file to get in the package
    - path_to_save: the path and name of the file to save
    """

    def search_file(package_dir, filename):
        for root, dirs, files in os.walk(package_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    if importlib.resources.is_resource("bibdata_management", path_to_find):
        content = importlib.resources.read_text("bibdata_management", path_to_find, encoding='utf-8-sig')
    else:
        pckg_dir = importlib.resources.files("bibdata_management")
        file_path = search_file(pckg_dir, path_to_find)
        if file_path is not None:
            content = importlib.resources.read_text("bibdata_management", file_path)
        else:
            return print(f"File '{path_to_find}' not found in the package.")

    if not op.isdir(Path(path_to_save).parent):
        os.mkdir(Path(path_to_save).parent)
    with open(path_to_save, 'w') as file:
        file.write(content)

    return


def handle_layer_string(tech_key):
    pattern = re.compile(r'layer', re.IGNORECASE)
    tech_key = pattern.sub('', tech_key)
    # Remove all punctuation except for the underscore
    translator = str.maketrans('', '', string.punctuation.replace('_', ''))
    tech_key = tech_key.translate(translator).strip()

    return tech_key
