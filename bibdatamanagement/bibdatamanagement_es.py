from bibdatamanagement.bibdatamanagement import *


class BibDataManagementES(BibDataManagement):
    def __init__(self, file_path, default_values=None):
        self.default_names = default_values
        self._db = self._get_bib_file_entries(file_path)
        self._df = self._translate_as_dataframe()

    def get_data(self, set_name=None, entry=None, category_name=None):
        """
            Returns a pandas DataFrame containing all data in the .bib file or a subset based on the given technology,
            set names or category names.

            Parameters
            -----------
            set_name : str, list, optional
                Name(s) of the set to filter by.
            entry : str, optional
                Name of the technology to filter by.
            category_name : str, list, optional
                Name(s) of the category to filter by.

            Returns
            --------
            pandas.DataFrame
                DataFrame containing the filtered data, or all data if no filters are applied.
        """

        df_to_return = self._df
        if entry:
            df_to_return = self.filter_by_entry(df_to_return, entry)
        if set_name:
            df_to_return = self.filter_by_set(df_to_return, set_name)
        if category_name:
            df_to_return = self.filter_by_category(df_to_return, category_name)

        return df_to_return

    def _get_bib_file_entries(self, bib_path):
        entries = []
        parser = bibtex.Parser()
        bib_data = parser.parse_file(bib_path)
        for el in bib_data.entries.keys():
            tech = {"cite_key": el, 'entry_type': bib_data.entries[el].type}
            note_format = ''
            if "annote" in bib_data.entries[el].fields:
                note_format = 'annote'
                notes_txt = bib_data.entries[el].fields['annote']
            elif "note" in bib_data.entries[el].fields:
                note_format = 'note'
                notes_txt = bib_data.entries[el].fields['note']
            else:
                continue
            n = re.findall("\+-(.*?)\+-", notes_txt)
            n = [re.sub(r'(\\)(\\\\)*(?!par|n|\\)', '', note) for note in n]
            if n:
                notes = []
                for elem in n:  # Une tech
                    elements = []
                    if note_format == 'note':
                        elements_tmp = elem.split("\\par")
                        if len(elements_tmp) < 2:
                            elements_tmp = elem.split("\\")
                    elif note_format == 'annote':
                        elements_tmp = elem.split("\\n")
                    for temp in elements_tmp:
                        if temp != "":
                            elements.append(temp.strip())
                    try:
                        category, name, row_name, sets, general_description, confidence, ref_year = \
                            self.read_entry_header(elements[0])
                    except Exception as e:
                        print(f'The error {e} occurred when trying to read header of the note:\n{elements[0]}\n'
                              f'From entry {tech["cite_key"]}\n')
                        continue

                    # Set paper fields
                    bib_element = ['title', 'year', 'month', 'abstract', 'annotation', 'file', 'doi', 'journal']
                    for bib_elem in bib_element:
                        if bib_elem in bib_data.entries[el].fields._keys.keys():
                            tech[bib_elem] = bib_data.entries[el].fields[bib_elem]
                        else:
                            tech[bib_elem] = None
                    if len(bib_data.entries[el].persons) > 0:
                        auth = bib_data.entries[el].persons['author']
                        tech['author'] = [str(a) for a in auth]

                    # Set year
                    if ref_year is None:
                        if 'year' in tech.keys() and tech['year'] is not None:
                            ref_year = extract_year(tech['year'])
                        else:
                            ref_year = datetime.now().year
                    else:
                        ref_year = datetime(int(ref_year), 1, 1).strftime("%Y")
                    if len(sets) == 0 or (len(sets) == 1 and sets[0] == ''):
                        note = {'category': category,
                                "entry": name,
                                'sets': ' ',
                                "general_description": general_description,
                                "rowname": row_name,
                                'confidence': confidence,
                                'reference_year': ref_year,
                                "keys": elements[1:]}
                        notes.append(note)
                    else:
                        for s in sets:
                            note = {'category': category,
                                    "entry": name,
                                    'sets': s,
                                    "general_description": general_description,
                                    "rowname": row_name,
                                    'confidence': confidence,
                                    'reference_year': ref_year,
                                    "keys": elements[1:]}
                            notes.append(note)

                tech["entries"] = notes

                entries.append(tech)

        return entries

    @staticmethod
    def read_entry_header(data):
        name = ""
        row_name = ""
        sets = []
        general_description = ""
        confidence = 1
        ref_year = None
        if "%" in data:
            parameters = data.split("%")
            category = parameters[0]
            parameters = parameters[1]
        else:
            category = 'Technology'
            parameters = data
        parameters = parameters.split("#")
        name = parameters[0].strip()
        if len(parameters) > 1:
            if len(parameters) > 2:
                confidence = parameters[2]
                if '=' in confidence:
                    confidence = confidence.split('=')[1]
                try:
                    confidence = float(confidence.strip())
                except ValueError:
                    confidence = 1
                if len(parameters) > 3:
                    ref_year = parameters[3]
                    if '=' in ref_year:
                        ref_year = ref_year.split('=')[1]
                    ref_year = float(ref_year.strip())
            technology_parameters = parameters[1].strip()
            parameters_elements = technology_parameters.split(":")
            row_name = parameters_elements[0].strip()
            if len(parameters_elements) == 2:
                sets_txt = parameters_elements[1].strip()
                if "[" in sets_txt and "]" in sets_txt:
                    sets_txt = sets_txt[1:-1]
                    sets_txt = sets_txt.split(",")
                    for set_value in sets_txt:
                        sets.append(set_value.strip())
                    sets = list(set(sets))
                else:
                    general_description = sets_txt.strip()
            elif len(parameters_elements) == 3:
                sets_txt = parameters_elements[1].strip()
                if "[" in sets_txt and "]" in sets_txt:
                    sets_txt = sets_txt[1:-1]
                    sets_txt = sets_txt.split(",")
                    for set_value in sets_txt:
                        sets.append(set_value.strip())
                    sets = list(set(sets))
                else:
                    sets = [sets_txt]
                general_description = parameters_elements[2].strip()
        return category, name, row_name, sets, general_description, confidence, ref_year

    def export_df(self, df, output_path, to):
        """
        Exports the given dataframe into a *.bib* file or an EnergyScope input file.

        Parameters
        -----------
        df : pd.DataFrame
            Dataframe to export.
        output_path : str
            Path of the file to save.
        to : str
            'bib' for a reference export, 'energyscope' for *.dat* file input.

        """
        if to == 'bib':
            self.export_df_to_bibtex(df, output_path)
        elif to == 'energyscope':
            # Look at if useful to choose were to write
            # caller_frame = inspect.stack()[1]
            # calling_file_path = os.path.dirname(caller_frame[1])
            file_path = Path(output_path)
            file_path.touch(exist_ok=True)
            with file_path.open('a') as file:
                for i, row in df.iterrows():
                    if 'LAYER' in row['entry_key'].upper():
                        tech_key = handle_layer_string(row['entry_key'])
                        line = 'let layers_in_out[\'{}\', \'{}\'] := {} ; # {} \n'. \
                            format(row['entry'], tech_key, row['value'], row['unit'])
                    else:
                        line = 'let {}[\'{}\'] := {} ; # {} \n'. \
                            format(row['entry_key'], row['entry'], row['value'], row['unit'])
                    file.write(line)
        return

    @staticmethod
    def filter_by_category(df, cat_name):
        return BibDataManagementES.filter_by(df, 'category', cat_name)
