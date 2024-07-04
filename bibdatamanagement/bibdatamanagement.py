import sys
from bibdatamanagement.utilities import *
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
        self._db = self._get_bib_file_entries(file_path)
        self._df = self._translate_as_dataframe()

    def add_default_values(self, pattern):
        """
        Adds an entry to the dataframe, from a string. The string should follow the usual syntax of Bibdatamanagement.

        Parameters
        ----------
        pattern : str
            A Bibdata entry, between +- to /+-

        Return
        --------
        str
            The name of the technology where default values have been added.

        Examples
        --------
        >>> tech_name = bib_object.add_default_values(
        ...        "+- enhOR# default: [default, energyscope]: that's my general description"
        ...        "cmaint = 0.5:1:2 [MCHF/(ktCO2*y)]"
        ...        "cinv = 0:1 [MCHF/(ktCO2*y)]"
        ...        "refsize = 0 [GW]"
        ...        "gwp = 0 [kgCO2/kWe]"
        ...        "lifetime = 0 [y]"
        ...        "CO2c = 0 [ktCO2]"
        ...        "+-")

        >>> tech_name
        enhOR

        Notes
        -----
        - The function returns the name of the technology but *in fine*, the whole entry was added to the instance df.
        """
        database = []
        default_tech = self._read_pattern(pattern)
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
                    "entry": tech['entry'],
                    'confidence': 1,
                    'reference_year': datetime.now().strftime('%Y'),
                    "entry_key": key["key"],
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
        df = df.set_index(["cite_key", 'entry', 'sets', 'entry_key', 'reference_year'], drop=False)
        self._df = pd.concat([self._df, df], axis=0)

        return df['entry'][0]

    def get_data(self, set_name=None, entry=None):
        """
        Returns a pandas DataFrame containing all data in the .bib file or a subset based on the given entry
        and set names.

        Parameters
        -----------
        set_name : str, optional
            Name of the set to filter by.
        entry : str, optional
            Name of the technology to filter by.

        Returns
        --------
        pandas.DataFrame
            DataFrame containing the filtered data, or all data if no filters are applied.

        See also
        --------
        filter_by

        Examples
        --------
        >>> bibdata = BibDataManagement(bib_file)
        >>> bib_df = bibdata.get_data(entry='WoodtoDiesel', set_name='first')

        >>> bib_df
                                             sets technology_key        value     unit
        cite_key             technology_name
        peduzzi_biomass_2015 WoodtoDiesel      []            trl     7.000000        -
                             WoodtoDiesel      []         cmaint    35.810000  MCHF/GW
                             WoodtoDiesel      []           cinv  1955.000000  MCHF/GW
                             WoodtoDiesel      []             cp     1.000000        -
                             WoodtoDiesel      []        refsize     0.001000       GW
                             WoodtoDiesel      []            gwp     0.000000   kt/GWh
                             WoodtoDiesel      []       lifetime    15.000000        y
                             WoodtoDiesel      []           Elec    -0.032695        -
        """
        df_to_return = self._df
        if entry:
            df_to_return = self.filter_by_entry(df_to_return, entry)
        if set_name:
            df_to_return = self.filter_by_set(df_to_return, set_name)

        return df_to_return

    def print_info_on_param(self, entry, set_name, parameter, lang='EN'):
        """
        Print information on the parameter retrieved for a given technology and set.

        Parameters
        ----------
        entry : str
            The name of the entry to select.
        set_name : str, list
            Name(s) of the set(s) to filter by. Can be '' if it has no set but cannot be None.
        parameter : str
            Name of the parameter on which to print the information.
        lang : str
             Language in which the info should be printed. Among ['FR', 'EN'].

        Returns
        -------
        The main information on the parameter asked

        Examples
        --------
        >>> bibdata.print_info_on_param(entry='enhOR', set_name='first', parameter='cinv')
        Parameter Investment Cost of enhOR
        Retrieved from: wang_review_2017
        URL: /Users/Wang et al. - 2017 - A Review of Post-combustion CO2 Capture Technologi.pdf;/Users/S1876610217313851.html
        Used in set(s): ['energyscope', 'first']
        That describes: a second comment
        Value = 1000.0 MCHF/(ktCO2*y)
        Over the whole bibliography, the parameter varies from 1000.0 to 1000.0 MCHF/(ktCO2*y)
        This information is annotated in the .bib in the following way:
        +- tech_name # row_name: [set, set]: general_description
        parameter = min:value:max [unit]
        +- tech_name
        """
        rows_tech = self.get_data(set_name=set_name, entry=entry)
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
                         "{} {}\n".format(words.loc[lang, 'tech'], row_to_print['entry']) +
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

    def statistics_by_tech_and_parameter(self, entry, parameter):
        rows_tech = self.get_data(entry=entry)
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
        stats['values'] = [rows_to_compute['value'].tolist()] * len(stats)
        stats['unit'] = rows_to_compute['unit'][0]

        return stats

    def statistics(self, df=None):
        """
        Compute statistics (min, max, median, average, number of values) for each parameter.

        Parameters
        ----------
        df : pd.DataFrame, optional
            A frame coming from BibData. If None, the self dataframe from the .bib file is used.

        Returns
        -------
             A dataframe indexed by entry and parameters with the statistics.

        Examples
        --------
        >>> bibdata = BibDataManagement(bib_file)
        >>> stats_df = bibdata.statistics()

        >>> stats_df
                                          min          max  ...  nvalues        values
        (WoodtoDiesel, trl)          7.000000     7.000000  ...        1         [7.0]
        (WoodtoDiesel, cmaint)      35.810000    35.810000  ...        1       [35.81]
        (WoodtoDiesel, cinv)      1955.000000  1955.000000  ...        1      [1955.0]
        (WoodtoDiesel, cp)           1.000000     1.000000  ...        1         [1.0]
        (WoodtoDiesel, refsize)      0.001000     0.001000  ...        1       [0.001]
        (WoodtoDiesel, gwp)          0.000000     0.000000  ...        1         [0.0]
        (WoodtoDiesel, lifetime)    15.000000    15.000000  ...        1        [15.0]
        (WoodtoDiesel, Elec)        -0.032695    -0.032695  ...        1  [-0.0326945]
        """
        stats = pd.DataFrame()
        if df is None:
            df = self._df
        for tech in df.index.get_level_values(level='entry').unique():
            for param in df.xs(tech, level='entry')['entry_key'].unique():
                stats = pd.concat([stats, self.statistics_by_tech_and_parameter(tech, param)])

        return stats

    def build_additional_set(self, df=None, from_stat='median'):
        """
        Adds another set to a DataFrame from a statistical criteria.

        Parameters
        ----------
        df : pd.DataFrame, optional
            A frame coming from BibData. If None, the self dataframe from the .bib file is used.
        from_stat : str, optional
            The statistic that will be used to add the rows. Choose among ['median', 'avg', 'weighted_avg', 'min', 'max'].

        Returns
        -------
            A DataFrame with the supplementary rows.

        Notes
        -----
        - The added rows have the value `from_stats` in the *sets* column.
        - The weigths used for the weighted average are the confidence given.

        Examples
        --------
        >>> df_with_avg = bib_object.build_additional_set(from_stat='avg')

        >>> df_with_avg
                                                                   cite_key  ...     short_name
        cite_key      technology_name technology_key                 ...
        my_paper_name avion           trl             my_paper_name  ...     tech_ready
                                      cmaint          my_paper_name  ...  my_param_name
                                      cinv            my_paper_name  ...           Cinv
                      avion           trl                            ...     tech_ready
                                      cmaint                         ...  my_param_name
                                      cinv                           ...           Cinv
        [6 rows x 28 columns]
        """
        valid_stats = ['median', 'avg', 'weighted_avg', 'min', 'max']
        if from_stat not in valid_stats:
            warnings.warn("Not a valid statistical indicator, please choose among {}".format(valid_stats))
        if df is None:
            df = self._df.copy()
        df_stats = self.statistics(df)
        medians = []
        for tech in df['entry'].unique():
            for param in df[df['entry'] == tech]['entry_key']:
                mask = (df['entry'] == tech) & (df['entry_key'] == param)
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
                                "entry": tech,
                                'confidence': 1,
                                'reference_year': datetime.now().strftime('%Y'),
                                "entry_key": param,
                                "min": df_stats.loc[(tech, param), 'min'],
                                "value": df_stats.loc[(tech, param), from_stat],
                                "max": df_stats.loc[(tech, param), 'max'],
                                "unit": df_stats.loc[(tech, param), 'unit'],
                                "short_name": df.loc[mask, 'short_name'][0],
                                "comment": from_stat + ' value'
                                })
        medians = pd.DataFrame.from_records(medians).drop_duplicates()
        medians[['min', 'value', 'max']] = medians[['min', 'value', 'max']].astype(float)
        medians = medians.set_index(["cite_key", 'entry', 'sets', 'entry_key', 'reference_year'], drop=False)

        return pd.concat([df, medians], axis=0)

    def parallel_coord(self, df=pd.DataFrame(), tech=None, params=None, color_by='paper', filename=None,
                       export_format='png', auto_open=True):
        """
        Visualisation of the values found in .bib for every parameter in a parallel plot coordinates, generated from plotly library.

        Parameters
        ----------
        df : pd.DataFrame, optional
            The data to plot. If not passed, tech and params can also be used.
        tech : str, optional
            The technology to filter the data by, if df is not given.
        params : list, optional
            List of string with the params to filter the data by, if df is not given.
        color_by : str, optional
            The variable to color the lines by. Among ['paper', 'tech', 'set', 'combined'].
        filename : str, optional
            The filename to save the plot.
        export_format : str, optional
            The format to save the plot. Among [png, jpg, html].
        auto_open : bool, optional
            Indicates whether to automatically open the plot.

        Returns
        ----------
        figure plotly object :
            An interactive parallel coordinates plot of the values that the technology has among the literature.

        Examples
        ----------
        >>> bib_object.parallel_coord()
        """
        traces = []
        if df.empty:
            df = self._df
        if tech:
            df = self.filter_by_technology(df, tech)
        tech_parameters = list(set(df['entry_key']))
        if params:
            for param in params:
                if param not in tech_parameters:
                    warnings.warn("The parameter {} is not among the ones detailed in bibliography".format(param))
                    params.remove(param)
        else:
            params = tech_parameters
        df.index = df.index.droplevel(['entry_key'])
        df_param = pd.DataFrame(columns=tech_parameters, index=df.index.unique())
        for param in tech_parameters:
            if param in params:
                try:
                    df_param[param] = df['value'][df['entry_key'] == param]
                except:
                    print(f'{param}')
                mean = df_param[param].dropna().mean()
                df_param[param].fillna(mean, inplace=True)
                trace = dict(label=param, values=df_param[param])
                traces.append(trace)
        mapping_paper = {k: v for k, v in zip(df_param.index.to_frame()['cite_key'],
                                              list(range(len(df_param.index.to_frame()['cite_key']))))}
        mapping_tech = {k: v for k, v in zip(df_param.index.to_frame()['entry'],
                                             list(range(len(df_param.index.to_frame()['entry']))))}
        mapping_set = {k: v for k, v in zip(df_param.index.to_frame()['sets'],
                                            list(range(len(df_param.index.to_frame()['sets']))))}
        frame = df_param.index.to_frame()
        traces.insert(0, dict(label='set',
                              ticktext=frame['sets'].unique(),
                              tickvals=frame['sets'].map(mapping_set).unique(),
                              values=frame['sets'].map(mapping_set),
                              # range=[-0.05, len(frame['entry'].unique()) * 1.05]
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
                              ticktext=frame['entry'].unique(),
                              tickvals=frame['entry'].map(mapping_tech).unique(),
                              values=frame['entry'].map(mapping_tech),
                              # range=[-0.05, len(frame['entry'].unique()) * 1.05]
                              )
                      )

        valid_color_options = ['paper', 'tech', 'set', 'combined']
        if color_by not in valid_color_options:
            color_by = 'paper'
            warnings.warn(print('The lines have been colored by paper as', color_by, 'is not among valid options:',
                                valid_color_options))
        dict_line_color = {'paper': frame['cite_key'].map(mapping_paper),
                           'tech': frame['entry'].map(mapping_tech),
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
            Visualisation of the values found in .bib for a given technology parameter in a histogram, generated from plotly library.

            Parameters
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

            Returns
            --------
            figure plotly object :
                An interactive histogram of the values that the technology parameter has among the literature.

            Examples
            --------
            >>> bib_object.param_histogram(tech='ANDIG', parameter='cinv')

            """
        df = self.filter_by_technology(self._df, tech)
        df = self.filter_by_param(df, parameter)
        if df.iloc[0]['short_name'] == '' or df.iloc[0]['short_name'] == ' ':
            title_key = df['entry_key'][0]
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

    def _translate_as_dataframe(self):
        database = []
        rowname = 1
        for entry in self._db:
            for tech in copy.deepcopy(entry['entries']):
                try:
                    tech["keys"] = list(map(self.read_tag, tech["keys"]))
                except Exception as e:
                    print(f'Error {e} occurred when reading the content of the note for:\n'
                          f'{tech["entry"]} of paper {entry["cite_key"]}\n')
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
                            # "entry": tech['technology'],
                            "entry_key": key["key"],
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
                            "entry": tech['technology'],
                            "entry_key": key["key"],
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
            subset=['cite_key', 'entry', 'sets', 'entry_key', 'reference_year'])
        col_double = ['cite_key', 'entry', 'sets', 'entry_key', 'min',
                      'value', 'max', 'confidence', 'reference_year']
        doubled_2 = df_translated.duplicated(col_double)
        mask = doubled & ~doubled_2
        if df_translated[mask].shape[0] > 0:
            for idx, row in df_translated[mask].iterrows():
                print(f'At least two different values were given for paper {row["cite_key"]}'
                      f' for the {row["entry"]} tech in set '
                      f'{row["sets"]} and parameter {row["entry_key"]}\n'
                      f'Only the 1st value was kept\n')
        df_translated = df_translated[~mask].drop_duplicates(col_double)
        if self.default_names:
            df_translated = self.fill_with_default(df_translated, self.default_names)

        return df_translated.set_index(["cite_key", 'entry', 'sets', 'entry_key', 'reference_year'],
                                       drop=False).fillna(" ")

    def _read_technology(self, technology_name, bib_path):
        techs = self._get_bib_file_entries(bib_path)
        techs = self._filter_bibdata_by_entry(techs, technology_name)
        return techs

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
                            self.read_entry_header(elements[0])
                    except Exception as e:
                        print(f'The error {e} occurred when trying to read header of the note:\n{elements[0]}\n'
                              f'From entry {tech["cite_key"]}\n')
                        continue

                    # Set paper fields
                    bib_element = ['title', 'year', 'month', 'abstract', 'annotation', 'file', 'doi', 'journal', 'howpublished']
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
                        note = {"entry": name,
                                'sets': ' ',
                                "general_description": general_description,
                                "rowname": row_name,
                                'confidence': confidence,
                                'reference_year': ref_year,
                                "keys": elements[1:]}
                        notes.append(note)
                    else:
                        for s in sets:
                            note = {"entry": name,
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

    def _filter_bibdata_by_entry(self, entries, entry):
        filtered_entries = []
        for tech in entries:
            entries = [t for t in tech["entries"] if t["entry"] == entry]
            if len(entries) > 0:
                tech["entries"] = entries[0]["keys"]
                tech["entries"] = list(map(self.read_tag, tech["entries"]))
                filtered_entries.append(tech)
        return filtered_entries

    def _read_pattern(self, pattern):
        rows = pattern.split("\n")
        entries = []
        already_read_header = False
        for row in rows:
            if "+-" in row:
                if row != "+-" and not already_read_header:
                    already_read_header = True
                    tech_params = row.split("+-")[1]
                    name, row_name, sets, general_description, confidence, ref_year = self.read_entry_header(
                        tech_params)
                    if len(sets) == 0:
                        entry = {"entry": name,
                                 'sets': ' ',
                                 "general_description": general_description,
                                 "rowname": row_name,
                                 'confidence': confidence,
                                 "keys": []}
                        if ref_year is None:
                            entry['reference_year'] = datetime.now().strftime("%Y")
                        else:
                            entry['reference_year'] = datetime(ref_year, 1, 1).strftime("%Y")
                        entries.append(entry)
                    else:
                        for s in sets:
                            entry = {"entry": name,
                                     'sets': s,
                                     "general_description": general_description,
                                     "rowname": row_name,
                                     'confidence': confidence,
                                     "keys": []}
                            if ref_year is None:
                                entry['reference_year'] = datetime.now().strftime("%Y")
                            else:
                                entry['reference_year'] = datetime(int(ref_year), 1, 1).strftime("%Y")
                            entries.append(entry)
            else:
                key = self.read_tag(row)
                if key is not None:
                    for entry in entries:
                        entry["keys"].append(key)
        return entries

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
    def read_entry_header(data):
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
    def filter_by_entry(df, tech):
        valid_entries = df.index.levels[1].tolist()
        low_valid_tech = [vt.lower() for vt in valid_entries]
        if tech.lower() in low_valid_tech:
            ind = low_valid_tech.index(tech.lower())
            return df.loc[(slice(None), valid_entries[ind]), :]
        else:
            warnings.warn('\n{} is not part of the entries in the .bib\n'.format(tech) +
                          'All techs have been kept\n' +
                          'Valid options are: {}'.format(valid_entries))
            return df

    @staticmethod
    def filter_by(df, column, criteria):
        """
        Used to filter the given DataFrame by a given colum and on given value(s) in that column.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame that should be filtered.
        column : str
            Name of the column to use for the filter.
        criteria : str or list
            Value(s) that the column should have to pass the filter.

        Returns
        -------
        A DataFrame where the rows not corresponding to the filter have been removed.

        Raises
        ------
        ValueError
            If the column name is not among the dataframe.
        Warns
        -----
        ValueError
            If the value given for the column are not valid ones. In that case the filter is not applied.

        See also
        --------
        filter_by_param, filter_by_entry, filter_by_set
        """
        def check_column(line):
            return ask_col == line

        if isinstance(criteria, str):
            ask_col = criteria
            mask = df[column].apply(check_column)
            df_to_return = df[mask]
        elif isinstance(criteria, list):
            mask = pd.Series(False, index=df[column].index)
            for ask_col in criteria:
                if sys.version_info >= (3, 9):
                    mask |= df[column].apply(check_column)
                else:
                    mask.update(df[column].apply(check_column))
            df_to_return = df[mask]
        else:
            warnings.warn('{} should be a string or a list of string.\n'.format(criteria) +
                          'The whole dataframe was returned.')
            return df

        if df_to_return.empty:
            valid_crits = []
            df['sets'].apply(lambda x: valid_crits.extend(x))
            valid_crits = list(set(valid_crits))
            warnings.warn('{} is not an existing set in this bib.\n'.format(criteria) +
                          'The whole dataframe was returned.' +
                          'Valid options are: {}'.format(valid_crits), category=ValueError)

            return df

        return df_to_return

    @staticmethod
    def filter_by_set(df, set_name):
        """
        Apply the ``filter_by`` method to the set column.
        """
        return BibDataManagement.filter_by(df, 'sets', set_name)

    @staticmethod
    def filter_by_param(df, parameter):
        """
        Apply the ``filter_by`` method to the *entry_key* column.
        """
        return BibDataManagement.filter_by(df, 'entry_key', parameter)

    @staticmethod
    def fill_with_default(df, default_file):
        df_description = file_reader(default_file)
        if df_description is None:
            return df
        df_translated = df.merge(df_description, left_on='entry_key', right_on='parameters')
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
        """
        Allows to merge together two BibDataManagement objects.

        Parameters
        -----------
        cls : BibDataManagement
            Self BibDataManagement instance.
        obj2: BibDataManagement
            The second instance that should be merged with the first one.

        Returns
        -------
        BibDataManagement
            A new BibDataManagement instance, resulting from the two references file.

        Examples
        --------
        >>> bib_obj1 = BibDataManagement('bibliography.bib', 'parameters_description.csv')
        >>> bib_obj2 = BibDataManagement('another_bibliography.bib', 'parameters_description.csv')
        >>> bib_full = bib_obj1.merge_bib(bib_obj2)
        """
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
        return

    @staticmethod
    def export_df_to_bibtex(df, output_path):
        """
        Exports the given dataframe into a *.bib* file, writing the data in the Notes section.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to export.
        output_path : str
            Path of the file to save.

        Notes
        -----
        - The path should end by *.bib*

        Examples
        ---------
        >>> bib_data = BibDataManagement('my_bib_file.bib')
        >>> stats = bib_data.build_additional_set(from_stat='avg')
        >>> bib_data.export_df_to_bibtex(stats, 'my_new_file.bib')
        Exported
        """
        def convert_param_into_annote(row, content_str):
            row[['min', 'value', 'max']] = row[['min', 'value', 'max']].astype(str)
            param_str = [row['entry_key'], "=", row['min'] + ":" + row['value'] + ":" + row['max'],
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
                for tech in ref_and_s['entry'].drop_duplicates():
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
