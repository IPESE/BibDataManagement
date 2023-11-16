import sys
from bibdata_management.utilities import *
# from utilities import *
import warnings
import plotly.graph_objects as go
from pybtex.database.input import bibtex
from pybtex.database import BibliographyData, Entry, Person
from datetime import datetime
import pandas as pd
import copy


class BibDataManagement:
    def __init__(self, file_path, default_values=None):
        self.default_names = default_values
        self.__db = self.__get_bib_file_technologies(file_path)
        self.__df = self.__translate_as_dataframe()

    def add_default_values(self, pattern):
        database = []
        default_tech = self.__read_pattern(pattern)
        for tech in default_tech:
            for key in tech["keys"]:
                database.append({
                    "cite_key": 'default',
                    "entry_type": "misc",
                    "title": None,
                    "year": datetime.now().strftime('%Y'),
                    "month": datetime.now().strftime('%B'),
                    "abstract": None,
                    "annotation": None,
                    "file": None,
                    "doi": None,
                    "journal": None,
                    "author": None,
                    "rowname": tech["rowname"],
                    "sets": tech["sets"],
                    "general_description": tech["general_description"],
                    "technology_name": tech['technology_name'],
                    'confidence': 1,
                    'reference_year': datetime.now().strftime('%Y'),
                    "technology_key": key["key"],
                    "min": key["min"],
                    "value": key["value"],
                    "max": key["max"],
                    "unit": key["unit"],
                    "short_name": key["short_name"],
                    "comment": key["description"]
                })
        df = pd.DataFrame.from_records(database)
        df[['min', 'value', 'max']] = df[['min', 'value', 'max']].astype(float)
        if self.default_names:
            df = self.fill_with_default(df, self.default_names)
            if df.shape[0] == 0:
                return print("You might want to check that the parameters description provided correspond the data.")
        df = df.set_index(["cite_key", 'technology_name', 'sets', 'technology_key'], drop=False)
        self.__df = pd.concat([self.__df, df], axis=0)

        return df['technology_name'][0]

    def get_data(self, set_name=None, tech_name=None):
        """
            Returns a pandas DataFrame containing all data in the .bib file or a subset based on the given technology
             and set names.

            Parameters:
            -----------
            set_name : str, optional
                Name of the set to filter by.
            tech_name : str, optional
                Name of the technology to filter by.

            Returns:
            --------
            pandas.DataFrame
                DataFrame containing the filtered data, or all data if no filters are applied. Df is indexed on paper
                 and technology.
        """
        df_to_return = self.__df
        if tech_name:
            df_to_return = self.filter_by_technology(df_to_return, tech_name)
        if set_name:
            df_to_return = self.filter_by_set(df_to_return, set_name)

        return df_to_return

    def print_info_on_param(self, tech_name, set_name, parameter, lang='EN'):
        rows_tech = self.get_data(set_name=set_name, tech_name=tech_name)
        row_to_print = self.filter_by_param(rows_tech, parameter)
        if row_to_print.shape[0] > 1:
            return print("Only one row can be printed")
        else:
            row_to_print = row_to_print.iloc[0]
            annote_en = str("Those information are annotated in the .bib in the following way:\n" +
                            "+- tech_name # row_name: [set, set]: general_description\n\\par\n" +
                            "parameter = min:value:max [unit]\n+- tech_name")
            annote_fr = str("Ces informations sont notés dans le .bib de la manière suivante:\n" +
                            "+- nom_tech # nom_ligne: [set, set]: description_generale\n\\par\n" +
                            "paramètre = min:valeur:max [unité]\n+- nom_tech")
            words = pd.DataFrame(columns=['param', 'tech', 'paper', 'set', 'description', 'value', 'min_max', 'annote'])
            words.loc['EN', :] = ['Parameter', 'of', 'Retrieved from', 'Used in set(s)', 'That describes',
                                  'Value', 'Over the whole bibliography, the parameter varies from',
                                  annote_en]
            words.loc['FR', :] = ['Paramètre', 'de', 'Extrait de', 'Utilisé dans les set(s)', 'Qui décrit',
                                  'Valeur', 'Sur l\'ensemble de la bibliographie, le paramètre varie de',
                                  annote_fr]
            # words = words.applymap(lambda x: x.encode('utf-8'))
            # TODO: find solution to print accents
            return print("{} {}".format(words.loc[lang, 'param'],
                                        row_to_print['long_name_' + lang]),
                         "{} {}\n".format(words.loc[lang, 'tech'], row_to_print['technology_name']) +
                         "{}: {}\n".format(words.loc[lang, 'paper'], row_to_print['cite_key']) +
                         "URL: {}\n".format(row_to_print['file']) +
                         "{}: {}\n".format(words.loc[lang, 'set'], row_to_print['sets']) +
                         "{}: {}\n\n".format(words.loc[lang, 'description'],
                                             row_to_print['description']) +
                         "{} = {} {}\n".format(words.loc[lang, 'value'],
                                               row_to_print['value'], row_to_print['unit']) +
                         "{} {} to {} {}\n\n".format(words.loc[lang, 'min_max'],
                                                     row_to_print['min'], row_to_print['max'], row_to_print['unit']
                                                     ) +
                         "{}".format(words.loc[lang, 'annote'])
                         )

    def statistics_by_tech_and_parameter(self, tech_name, parameter):
        rows_tech = self.get_data(tech_name=tech_name)
        rows_to_compute = self.filter_by_param(rows_tech, parameter)
        stats = pd.DataFrame(index=rows_to_compute.droplevel(['cite_key', 'sets']).index.drop_duplicates(),
                             columns=['min', 'max', 'median', 'avg', 'weighted_avg', 'nvalues', 'values'])
        stats['min'] = rows_to_compute['value'].min()
        stats['max'] = rows_to_compute['value'].max()
        stats['median'] = rows_to_compute['value'].median()
        stats['avg'] = rows_to_compute['value'].mean()
        stats['weighted_avg'] = (rows_to_compute['confidence'] * rows_to_compute['value']).sum() \
                                / rows_to_compute['confidence'].sum()
        stats['nvalues'] = rows_to_compute.shape[0]
        stats['values'] = [rows_to_compute['value'].tolist()]
        stats['unit'] = rows_to_compute['unit'][0]

        return stats

    def statistics(self, df=None):
        """
            Compute statistics (min, max, median, average, number of values) for each parameter

            Return:
                 A dataframe indexed by technology_name and parameters with the statistics
        """
        stats = pd.DataFrame()
        if df is None:
            df = self.__df
        for tech in df.index.get_level_values(level='technology_name').unique():
            for param in df.xs(tech, level='technology_name')['technology_key'].unique():
                stats = pd.concat([stats, self.statistics_by_tech_and_parameter(tech, param)])

        return stats

    def build_additional_set(self, df=None, from_stat='median'):
        valid_stats = ['median', 'avg', 'weighted_avg', 'min', 'max']
        if from_stat not in valid_stats:
            warnings.warn("Not a valid statistical indicator, please choose among {}".format(valid_stats))
        if df is None:
            df = self.__df.copy()
        df_stats = self.statistics(df)
        medians = []
        for tech in df['technology_name'].unique():
            for param in df[df['technology_name'] == tech]['technology_key']:
                mask = (df['technology_name'] == tech) & (df['technology_key'] == param)
                medians.append({'cite_key': '',
                                "entry_type": "misc",
                                'title': None,
                                "year": datetime.now().strftime('%Y'),
                                "month": datetime.now().strftime('%B'),
                                "abstract": None,
                                "annotation": None,
                                "file": None,
                                "doi": None,
                                "journal": None,
                                "author": None,
                                "rowname": from_stat,
                                "sets": from_stat,
                                "general_description": 'Median set built with every values',
                                "technology_name": tech,
                                'confidence': 1,
                                'reference_year': datetime.now().strftime('%Y'),
                                "technology_key": param,
                                "min": df_stats.loc[(tech, param), 'min'],
                                "value": df_stats.loc[(tech, param), from_stat],
                                "max": df_stats.loc[(tech, param), 'max'],
                                "unit": df_stats.loc[(tech, param), 'unit'],
                                "short_name": df.loc[mask, 'short_name'][0],
                                "comment": from_stat + ' value'
                                })
        medians = pd.DataFrame.from_records(medians).drop_duplicates()
        medians[['min', 'value', 'max']] = medians[['min', 'value', 'max']].astype(float)
        medians = medians.set_index(["cite_key", 'technology_name', 'sets', 'technology_key'], drop=False)

        return pd.concat([df, medians], axis=0)

    def parallel_coord(self, df=pd.DataFrame(), tech=None, params=None, color_by='paper', filename=None,
                       export_format='png', auto_open=True):
        """
            Create a parallel coordinates plot for a given bibliography.

            Parameters:
            ----------
            - df (optional): a dataframe that will be plotted. If not passed, tech and params can also be used
            - tech (optional): a string representing the technology to filter the data by
            - params (optional): a list of string with the params to filter the data by
            - color_by (optional): a string representing the variable to color the lines by, ['paper', 'tech', 'set', 'combined']
            - filename (optional): a string representing the filename to save the plot as
            - export_format (optional): a string representing the format to save the plot in (png, jpg, html)
            - auto_open (optional): a boolean indicating whether to automatically open the plot

            Returns:
            ----------
            - Write the plot
            - fig object
            """
        traces = []
        if df.empty:
            df = self.__df
        if tech:
            df = self.filter_by_technology(df, tech)
        tech_parameters = list(set(df['technology_key']))
        if params:
            for param in params:
                if param not in tech_parameters:
                    warnings.warn("The parameter {} is not among the ones detailed in bibliography".format(param))
                    params.remove(param)
        else:
            params = tech_parameters
        df.index = df.index.droplevel(['technology_key'])
        df_param = pd.DataFrame(columns=tech_parameters, index=df.index.unique())
        for param in tech_parameters:
            if param in params:
                try:
                    df_param[param] = df['value'][df['technology_key'] == param]
                except:
                    print(f'{param}')
                mean = df_param[param].dropna().mean()
                df_param[param].fillna(mean, inplace=True)
                trace = dict(label=param, values=df_param[param])
                traces.append(trace)
        mapping_paper = {k: v for k, v in zip(df_param.index.to_frame()['cite_key'],
                                              list(range(len(df_param.index.to_frame()['cite_key']))))}
        mapping_tech = {k: v for k, v in zip(df_param.index.to_frame()['technology_name'],
                                             list(range(len(df_param.index.to_frame()['technology_name']))))}
        mapping_set = {k: v for k, v in zip(df_param.index.to_frame()['sets'],
                                            list(range(len(df_param.index.to_frame()['sets']))))}
        frame = df_param.index.to_frame()
        traces.insert(0, dict(label='set',
                              ticktext=frame['sets'].unique(),
                              tickvals=frame['sets'].map(mapping_set).unique(),
                              values=frame['sets'].map(mapping_set),
                              # range=[-0.05, len(frame['technology_name'].unique()) * 1.05]
                              )
                      )
        traces.insert(0, dict(label='paper',
                              ticktext=frame['cite_key'].unique(),
                              tickvals=frame['cite_key'].map(mapping_paper).unique(),
                              values=frame['cite_key'].map(mapping_paper),
                              # range=[-0.05, len(frame['cite_key'].unique())]
                              )
                      )
        traces.insert(0, dict(label='technology',
                              ticktext=frame['technology_name'].unique(),
                              tickvals=frame['technology_name'].map(mapping_tech).unique(),
                              values=frame['technology_name'].map(mapping_tech),
                              # range=[-0.05, len(frame['technology_name'].unique()) * 1.05]
                              )
                      )

        valid_color_options = ['paper', 'tech', 'set', 'combined']
        if color_by not in valid_color_options:
            color_by = 'paper'
            warnings.warn(print('The lines have been colored by paper as', color_by, 'is not among valid options:',
                                valid_color_options))
        dict_line_color = {'paper': frame['cite_key'].map(mapping_paper),
                           'tech': frame['technology_name'].map(mapping_tech),
                           'set': frame['sets'].map(mapping_set),
                           'combined': list(range(frame.shape[0]))
                           }
        fig = go.Figure(data=
        go.Parcoords(
            line=dict(color=dict_line_color[color_by], colorscale='Jet'),
            dimensions=traces
        )
        )
        self.export_plot(fig, filename, export_format)
        if auto_open:
            fig.show()

        return fig

    def param_histogram(self, tech, parameter, filename=None, export_format='png', auto_open=True):
        """
            Generates a histogram plot of a parameter values for a given technology.

            Parameters:
            -----------
            tech: str
                The technology name to filter the data on.
            parameter: str
                The parameter name to filter the data on.
            filename: str, optional (default=None)
                The filename to save the exported plot as. If None, the plot is not exported.
            export_format: str, optional (default='png')
                The file format to export the plot in. Only applicable if `filename` is provided. Supported formats are 'png', 'jpeg', 'webp', 'svg', 'pdf'.
            auto_open: bool, optional (default=True)
                Whether to automatically open the plot in a new browser tab.

            Returns:
            --------
            figure plotly object

            """
        df = self.filter_by_technology(self.__df, tech)
        df = self.filter_by_param(df, parameter)
        if df.iloc[0]['short_name'] == '' or df.iloc[0]['short_name'] == ' ':
            title_key = df['technology_key'][0]
        else:
            title_key = df['short_name'][0]
        layout = go.Layout(title='Histogram of different {} values'.format(title_key),
                           xaxis=dict(title='Value {}'.format(df.iloc[0]['unit'])), yaxis=dict(title='Occurences'))
        figure = go.Figure(data=go.Histogram(
            x=df['value'], nbinsx=5,
            # customdata=df['sets'],
            # hovertemplate='<b>Value = %{x}</b><br>' +
            #               '<i>From paper: %{text}</i><br>' +
            #               'And set: %{customdata}'
        ), layout=layout)
        self.export_plot(figure, filename, export_format)
        if auto_open:
            figure.show()

        return figure

    def __translate_as_dataframe(self):
        database = []
        rowname = 1
        for entry in self.__db:
            for tech in copy.deepcopy(entry['technologies']):
                try:
                    tech["keys"] = list(map(self.read_tag, tech["keys"]))
                except Exception as e:
                    print(f'Error {e} occurred when reading the content of the note for:\n'
                          f'{tech["technology_name"]} of paper {entry["cite_key"]}\n')
                    continue
                for key in tech['keys']:
                    if tech["rowname"] != "":
                        rowname = rowname - 1
                    tech['rowname'] = str(rowname) if tech["rowname"] == "" else tech["rowname"]
                    bib_element = {key: value for key, value in entry.items()}
                    bib_element.popitem()
                    if sys.version_info >= (3, 9):
                        bib_element |= {key: value for key, value in tech.items()}
                        bib_element.popitem()
                        bib_element |= {
                            # "technology_name": tech['technology'],
                            "technology_key": key["key"],
                            "min": key["min"],
                            "value": key["value"],
                            "max": key["max"],
                            "unit": key["unit"],
                            "short_name": key["short_name"],
                            "comment": key["description"]
                        }
                        if key['confidence'] is not None:
                            bib_element |= {'confidence': key['confidence']}
                    else:
                        bib_element.update({
                            "technology_name": tech['technology'],
                            "technology_key": key["key"],
                            "min": key["min"],
                            "value": key["value"],
                            "max": key["max"],
                            "unit": key["unit"],
                            "short_name": key["short_name"],
                            "comment": key["description"]
                        })
                        if key['confidence'] is not None:
                            bib_element.update({'confidence': key['confidence']})
                    database.append(bib_element)
                    rowname = rowname + 1
        df_translated = pd.DataFrame.from_records(database)
        df_translated[['min', 'value', 'max']] = df_translated[['min', 'value', 'max']].astype(float)
        # df_translated['sets'] = df_translated['sets'].astype(str)

        doubled = df_translated.duplicated(
            subset=['cite_key', 'technology_name', 'sets', 'technology_key'])
        col_double = ['cite_key', 'technology_name', 'sets', 'technology_key', 'min',
                      'value', 'max', 'confidence', 'reference_year']
        doubled_2 = df_translated.duplicated(col_double)
        mask = doubled & ~doubled_2
        if df_translated[mask].shape[0] > 0:
            for idx, row in df_translated[mask].iterrows():
                print(f'At least two different values were given for paper {row["cite_key"]}'
                      f' for the {row["technology_name"]} tech in set '
                      f'{row["sets"]} and parameter {row["technology_key"]}\n'
                      f'Only the 1st value was kept\n')
        df_translated = df_translated[~mask].drop_duplicates(col_double)
        if self.default_names:
            df_translated = self.fill_with_default(df_translated, self.default_names)

        return df_translated.set_index(["cite_key", 'technology_name', 'sets', 'technology_key'], drop=False).fillna(
            " ")

    def __read_technology(self, technology_name, bib_path):
        techs = self.__get_bib_file_technologies(bib_path, technology_name)
        techs = self.__filter_technologies_by_technology_name(techs, technology_name)
        return techs

    def __get_bib_file_technologies(self, bib_path):
        technologies = []
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
            n = re.findall("\+- (.*?) \+-", notes_txt)
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
                        name, row_name, sets, general_description, confidence, ref_year = \
                            self.read_technology_header(elements[0])
                    except Exception as e:
                        print(f'The error {e} occurred when trying to read header of the note:\n{elements[0]}\n'
                              f'From entry {tech["cite_key"]}\n')
                        continue

                    if len(sets) == 0:
                        note = {"technology_name": name,
                                'sets': ' ',
                                "general_description": general_description,
                                "rowname": row_name,
                                'confidence': confidence,
                                "keys": elements[1:]}
                        notes.append(note)
                    else:
                        for s in sets:
                            note = {"technology_name": name,
                                    'sets': s,
                                    "general_description": general_description,
                                    "rowname": row_name,
                                    'confidence': confidence,
                                    "keys": elements[1:]}
                            notes.append(note)
                bib_element = ['title', 'year', 'month', 'abstract', 'annotation', 'file', 'doi', 'journal']
                for bib_elem in bib_element:
                    if bib_elem in bib_data.entries[el].fields._keys.keys():
                        tech[bib_elem] = bib_data.entries[el].fields[bib_elem]
                    else:
                        tech[bib_elem] = None
                if len(bib_data.entries[el].persons) > 0:
                    auth = bib_data.entries[el].persons['author']
                    tech['author'] = [str(a) for a in auth]
                if ref_year is None:
                    tech['reference_year'] = tech['year']
                else:
                    tech['reference_year'] = ref_year
                tech["technologies"] = notes

                technologies.append(tech)

        return technologies

    def __filter_technologies_by_technology_name(self, techs, technology_name):
        filtered_technologies = []
        for tech in techs:
            technologies = [t for t in tech["technologies"] if t["technology"] == technology_name]
            if len(technologies) > 0:
                tech["technologies"] = technologies[0]["keys"]
                tech["technologies"] = list(map(self.read_tag, tech["technologies"]))
                filtered_technologies.append(tech)
        return filtered_technologies

    def __read_pattern(self, pattern):
        rows = pattern.split("\n")
        technologies = []
        already_read_header = False
        for row in rows:
            if "+-" in row:
                if row != "+-" and not already_read_header:
                    already_read_header = True
                    tech_params = row.split("+-")[1]
                    name, row_name, sets, general_description, confidence, ref_year = self.read_technology_header(
                        tech_params)
                    if len(sets) == 0:
                        technology = {"technology_name": name,
                                      'sets': ' ',
                                      "general_description": general_description,
                                      "rowname": row_name,
                                      'confidence': confidence,
                                      "keys": []}
                        if ref_year is None:
                            technology['reference_year'] = datetime.now().year
                        else:
                            technology['reference_year'] = ref_year
                        technologies.append(technology)
                    else:
                        for s in sets:
                            technology = {"technology_name": name,
                                          'sets': s,
                                          "general_description": general_description,
                                          "rowname": row_name,
                                          'confidence': confidence,
                                          "keys": []}
                            if ref_year is None:
                                technology['reference_year'] = datetime.now().year
                            else:
                                technology['reference_year'] = ref_year
                            technologies.append(technology)
            else:
                key = self.read_tag(row)
                if key is not None:
                    for technology in technologies:
                        technology["keys"].append(key)  
        return technologies

    @staticmethod
    def read_tag(data):
        key = {}
        confidence = None
        if "#" in data:
            param_elements = data.split("#")
            val = param_elements[0]
            desc = param_elements[1]
            if len(param_elements) == 3:
                confidence = param_elements[2]
                if '=' in confidence:
                    confidence = confidence.split('=')[1]
                confidence = float(confidence.strip())
            if ":" in desc:
                short_name, description = desc.split(":")
                short_name = short_name.strip()
                description = description.strip()
                if short_name == '':
                    short_name = None
            else:
                short_name = None
                description = desc.strip()
            if description == '':
                description = None
        else:
            description = None
            short_name = None
            val = data
        if val != "":
            name, value, unit = re.findall(r"^(.*)\s*=\s*(.*)\s*\[(.*)\]", val)[0]
            if 'LAYER' in name.upper():
                name = handle_layer_string(name) + ' (layer)'
            key["key"] = name.strip()
            value = value.strip()
            unit = unit.strip()
            if ":" in value:
                values = value.split(":")
                if len(values) == 3:
                    key["min"] = values[0]
                    key["value"] = values[1]
                    key["max"] = values[2]
                elif len(values) == 2:
                    key["min"] = values[0]
                    key["value"] = values[1]
                    key["max"] = values[1]
            else:
                key["min"] = value
                key["value"] = value
                key["max"] = value
            key["unit"] = unit
            key["short_name"] = short_name
            key["description"] = description
            key["confidence"] = confidence
            return key

    @staticmethod
    def read_technology_header(data):
        name = ""
        row_name = ""
        sets = []
        general_description = ""
        confidence = 1
        ref_year = None
        parameters = data.split("#")
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
        return name, row_name, sets, general_description, confidence, ref_year

    @staticmethod
    def filter_by_technology(df, tech):
        valid_technologies = df.index.levels[1].tolist()
        low_valid_tech = [vt.lower() for vt in valid_technologies]
        if tech.lower() in low_valid_tech:
            ind = low_valid_tech.index(tech.lower())
            return df.loc[(slice(None), valid_technologies[ind]), :]
        else:
            warnings.warn('\n{} is not part of the technologies in the .bib\n'.format(tech) +
                          'All techs have been kept\n' +
                          'Valid options are: {}'.format(valid_technologies))
            return df

    @staticmethod
    def filter_by_set(df, set_name):
        def check_set(line):
            return ask_set == line

        if isinstance(set_name, str):
            ask_set = set_name
            mask = df['sets'].apply(check_set)
            df_to_return = df[mask]
        elif isinstance(set_name, list):
            mask = pd.Series(False, index=df['sets'].index)
            for ask_set in set_name:
                if sys.version_info >= (3, 9):
                    mask |= df['sets'].apply(check_set)
                else:
                    mask.update(df['sets'].apply(check_set))
            df_to_return = df[mask]
        else:
            warnings.warn('{} should be a string or a list of string.\n'.format(set_name) +
                          'The whole dataframe was returned.')
            return df
        if df_to_return.empty:
            valid_sets = []
            df['sets'].apply(lambda x: valid_sets.extend(x))
            valid_sets = list(set(valid_sets))
            warnings.warn('{} is not an existing set in this bib.\n'.format(set_name) +
                          'The whole dataframe was returned.' +
                          'Valid options are: {}'.format(valid_sets))

            return df

        return df_to_return

    @staticmethod
    def filter_by_param(df, parameter):
        df_filtered = df[df['technology_key'] == parameter]
        if df_filtered.empty:
            warnings.warn(
                f"The parameter is not among the existing one for that technology.\n Choose among those options:"
                f"{df['technology_key'].unique()}", category=UserWarning)

        return df_filtered

    @staticmethod
    def fill_with_default(df, default_file):
        df_description = file_reader(default_file)
        if df_description is None:
            return df
        df_translated = df.merge(df_description, left_on='technology_key', right_on='parameters')
        df_translated = keep_reference_df(df_translated)

        return df_translated

    @staticmethod
    def export_plot(fig, filename, export_format):
        valid_format_options = ['png', 'jpg', 'html']
        if filename:
            if isinstance(filename, str):
                if export_format in valid_format_options:
                    if export_format == 'png' or export_format == 'jpg':
                        fig.write_image(filename + '.' + export_format)
                    else:
                        fig.write_html(filename + '.' + export_format)
                else:
                    warnings.warn(print('Plot was exported png as', export_format, 'is not among valid options:',
                                        valid_format_options))
                    fig.write_image(filename + '.png')
            else:
                warnings.warn('Filename should be a string')

    @classmethod
    def merge_bib(cls, obj2):
        new_df = pd.concat([cls.__df.get_data(), obj2.get_data()])
        double = new_df.drop('sets', axis=1).duplicated()
        cls.__df = new_df[double]
        new_db = []
        not_duplicated = True
        for dico2 in obj2.__db:
            for dico in cls.__db:
                if list(dico.values()) == list(dico2.values()):
                    not_duplicated = False
            if not_duplicated:
                new_db.append(dico2)
        [new_db.append(db) for db in cls.__db]
        cls.__db = new_db
        return cls

    def export_df_to(self, df, output_path, to):
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
                    if 'LAYER' in row['technology_key'].upper():
                        tech_key = handle_layer_string(row['technology_key'])
                        line = 'let layers_in_out[\'{}\', \'{}\'] := {} ; # {} \n'. \
                            format(row['technology_name'], tech_key, row['value'], row['unit'])
                    else:
                        line = 'let {}[\'{}\'] := {} ; # {} \n'. \
                            format(row['technology_key'], row['technology_name'], row['value'], row['unit'])
                    file.write(line)
        return

    @staticmethod
    def export_df_to_bibtex(df, output_path):
        def convert_param_into_annote(row, content_str):
            row[['min', 'value', 'max']] = row[['min', 'value', 'max']].astype(str)
            param_str = [row['technology_key'], "=", row['min'] + ":" + row['value'] + ":" + row['max'],
                         "[" + row['unit'] + "]"]
            if row['short_name'] != ' ':
                param_str.append(row['short_name'])
                if row['description'] != ' ':
                    param_str.append(": " + row['description'])
            param_str = " ".join(param_str)
            content_str.append(param_str)
            return content_str

        # TODO: Missing author in reference and journal
        paper_col = ['title', 'year', 'month', 'abstract', 'annotation', 'file', 'doi', 'journal']

        bib_data = BibliographyData()
        for paper in df['cite_key'].drop_duplicates():
            ref = df.xs(paper, level='cite_key')
            note = []
            for s in ref['sets']:
                ref_and_s = ref.xs(s, level='sets')
                for tech in ref_and_s['technology_name'].drop_duplicates():
                    param = ref_and_s.loc[tech, :]
                    first_row = param.iloc[0]

                    header = ['', '', '']
                    sep = ['', '', '']
                    if not first_row['rowname'].isdigit() or first_row['sets'] != ' ' or first_row[
                        'general_description'] != ' ':
                        sep[0] = ' # '
                        if not first_row['rowname'].isdigit():
                            header[0] = f'{first_row["rowname"]}:{first_row["sets"]}:{first_row["general_description"]}'
                        else:
                            header[0] = f'{first_row["rowname"]}:{first_row["sets"]}:{first_row["general_description"]}'
                    if first_row['confidence'] != 1:
                        sep = [" # ", " # ", '']
                        header[1] = f'confidence = {first_row["confidence"]}'
                    if first_row['reference_year'] != first_row['year']:
                        sep = [" # ", " # ", " # "]
                        header[2] = f'ref_year = {first_row["ref_year"]}'

                    title = f"+- {tech}{sep[0]}{header[0]}{sep[1]}{header[1]}{sep[2]}{header[2]}\n"
                    content = []
                    param.apply(lambda x: convert_param_into_annote(x, content), axis=1)
                    content.append("+- /" + tech)
                    content.insert(0, title)
                    content = " \\par\n".join(content)
                    note.append(content)
            note = " \\par\n".join(note)
            first_row = ref.iloc[0]
            fields = {col: value for col, value in first_row.loc[paper_col].items()}
            fields['note'] = note
            authors = [Person(auth) for auth in first_row.loc['author']]
            entry = Entry(first_row['entry_type'], fields=fields, persons={'author': authors})
            bib_data.add_entry(first_row['cite_key'], entry)

        with open(output_path, 'w') as bib_file:
            str_to_export = re.sub(r'\\#', '#', bib_data.to_string('bibtex'))
            bib_file.write(str_to_export)

        return print("Exported")
