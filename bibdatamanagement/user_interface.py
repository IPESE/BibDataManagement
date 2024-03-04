import pickle
import warnings
from bibdatamanagement.bibdatamanagement import BibDataManagement
from bibdatamanagement.utilities import *


class RBibData:
    def __init__(self, bib_path, default_path=None):
        self.__bibdata = BibDataManagement(bib_path, default_path)
        self.__selected_data = {'tech': {'name': [], 'parameters': []}, 'sets': []}
        self.current_df = pd.DataFrame()

    @property
    def bibdata(self):
        return self.__bibdata

    @bibdata.setter
    def bibdata(self, value):
        if type(value) is BibDataManagement:
            self.__bibdata = value
        else:
            raise TypeError("Expected BibDataManagement object")

    @property
    def selected_data(self):
        return self.__selected_data

    @bibdata.setter
    def selected_data(self, value):
        if type(value) is dict:
            self.__selected_data = value
        else:
            raise TypeError("Expected dict of tech and sets")

    def read_chunk(self, code):
        chunk = Chunk(code)
        if chunk.manager == ':' or chunk.manager == '!':
            return self.manage_bibdata(chunk)
        else:
            self.__bibdata.add_default_values(chunk.content)
            return chunk.display

    def manage_bibdata(self, chunk):
        functionality, arguments, selection = self.__read_title(chunk.title)
        if chunk.content != "":
            self.__bibdata.add_default_values(chunk.content)
        if functionality.lower() == "select":
            res, foot = self.display_bibdata(arguments, selection)
            return chunk.display, "custom_view", res, foot
        elif functionality.lower() == "save":
            self.save_bibdata(arguments)
            return chunk.display, ""
        elif functionality.lower() == "load":
            self.load_bibdata(arguments)
            return chunk.display, ""
        elif "parcoords" in functionality.lower():
            fig = self.parcoords_bibdata(functionality, selection, arguments)
            return chunk.display, "plot", fig
        elif "histogram" in functionality.lower():
            fig = self.histogram_bibdata(functionality, selection, arguments)
            return chunk.display, "plot", fig

        return chunk.display, functionality, chunk.content

    def parcoords_bibdata(self, functionality, selection, arguments):
        df = self.__select_bibdata(selection)
        dict_plot = {'color_by': 'paper', 'export_format': 'html'}
        if "*" in functionality:
            if functionality.split("*")[1]:
                dict_plot['filename'] = functionality.split("*")[1]
            else:
                dict_plot['filename'] = './tmp/parcoords'
        else:
            dict_plot['filename'] = None
        if arguments:
            for arg in arguments:
                if arg == 'tech':
                    dict_plot['color_by'] = 'tech'
                elif arg == 'both':
                    dict_plot['color_by'] = 'both'
                elif arg == 'png':
                    dict_plot['export_format'] = 'png'
                elif arg == 'html':
                    dict_plot['export_format'] = 'html'
        fig = self.__bibdata.parallel_coord(df, color_by=dict_plot['color_by'],
                                            export_format=dict_plot['export_format'],
                                            filename=dict_plot['filename'],
                                            auto_open=False)

        fig_json = self.convert_json_to_r(fig.to_json())

        return fig_json

    def histogram_bibdata(self, functionality, selection, arguments):
        dict_plot = {'export_format': 'html'}
        if "*" in functionality:
            if functionality.split("*")[1]:
                dict_plot['filename'] = functionality.split("*")[1]
            else:
                dict_plot['filename'] = './tmp/parcoords'
        else:
            dict_plot['filename'] = None
        if arguments:
            for arg in arguments:
                if arg == 'png':
                    dict_plot['export_format'] = 'png'
                elif arg == 'html':
                    dict_plot['export_format'] = 'html'
        if len(selection['tech']['name']) == 1 and len(selection['tech']['parameters'][0]) == 1\
                and selection['tech']['parameters'][0][0] != 'all':
            fig = self.__bibdata.param_histogram(tech=selection['tech']['name'][0],
                                                 parameter=selection['tech']['parameters'][0][0],
                                                 export_format=dict_plot['export_format'],
                                                 filename=dict_plot['filename'], auto_open=False)

            fig_json = self.convert_json_to_r(fig.to_json())

            return fig_json
        else:
            return print("Only one parameter for one technology can be plotted as an histogram.")

    def save_bibdata(self, arguments):
        if not op.isdir("./temp"):
            os.mkdir("./temp")
        if not arguments:
            arguments = 'bib'
        arguments = [par.lower().strip() for par in arguments.split(",")]
        if 'data' in arguments:
            with open("./temp/bibdata.pickle", "wb") as data_file:
                pickle.dump(self.current_df, data_file)
        if 'bib' in arguments:
            self.__bibdata.export_df_to(self.current_df, "./temp/References.bib", 'bib')
        if 'energyscope' in arguments:
            self.__bibdata.export_df_to(self.current_df, "./temp/tech_values.dat", 'energyscope')

    def load_bibdata(self, arguments):
        if not arguments:
            arguments = 'bib'
        if 'data' in arguments:
            self.selected_data = pd.read_pickle("./temp/bibdata.pickle")
            self.__select_bibdata(self.__selected_data)
        if 'bib' in arguments:
            self.bibdata = BibDataManagement("./temp/References.bib")

    def display_bibdata(self, header, selection):
        # TODO: When launching the model or saving the data, do something so that if the number of value that the model
        # can take is more than one, compute the mean 
        arguments = ['entry', 'short_name', 'value', 'unit', 'comment', 'description', 'cite_key']
        bibdata_columns = ['entry', 'short_name', 'value', 'unit', 'comment', 'description', 'sets',
                           'cite_key']
        print_columns = ['Technology', 'Parameter', 'Value', 'Unit', 'Comment', 'Description', 'Set', 'Reference']
        translate_col = dict(zip(bibdata_columns, print_columns))
        stats = ''
        if header:
            if ',' in header:
                display_options = header.split(",")[0]
                stats = header.split(",")[1].strip()
            else:
                display_options = header
            arguments = []
            for chars in display_options:
                if chars == "t":
                    arguments.append("entry")
                if chars == "n":
                    arguments.append("short_name")
                elif chars == "v":
                    arguments.append("value")
                elif chars == "u":
                    arguments.append("unit")
                elif chars == "d":
                    arguments.append("description")
                elif chars == "c":
                    arguments.append("comment")
                elif chars == "s":
                    arguments.append("sets")
                elif chars == "r":
                    arguments.append("cite_key")

        df = self.__select_bibdata(selection)
        if stats != '':
            df = self.__bibdata.build_additional_set(df, stats)
            self.current_df = df[df['sets'] == stats].copy()
        else:
            self.current_df = df.copy()
            
        if 'description' in arguments:
            footnote = []
        else:
            footnote = None
        df = df.sort_index()
        for i, row in df.iterrows():
            if 'cite_key' in arguments:
                df.loc[i, 'cite_key'] = "@" + row['cite_key'] if row['rowname'] != stats else row['cite_key']
            if 'description' in arguments and 'description' in df.columns:
                if row['description'] != " ":
                    footnote.append(row['short_name'] + ": " + row['description'])
                    footnote = list(set(footnote))
            if 'sets' in arguments:
                if row['sets'] == ' ':
                    df.loc[i, 'sets'] = '-'
            if 'value' in arguments:
                val = str(round(row['value'], 2))
                if row['min'] != row['value'] and row['max'] != row['value']:
                    val = f'{val} \u2208 [{row["min"]}; {row["max"]}]'
                elif row['min'] != row['value']:
                    val = f'{val} \u2208 [{row["min"]}; +\u221e)'
                elif row['max'] != row['value']:
                    val = f'{val} \u2208 (-\u221e; {row["max"]}]'
                df.loc[i, 'value'] = val
        
        if 'description' in arguments:
            arguments.remove('description')
            
        df = df.sort_index(level=['entry', 'entry_key'])
        df = df.loc[:, arguments].rename(columns=translate_col).fillna(" ")

        return df, footnote

    def __select_bibdata(self, selection):

        df_tech = pd.DataFrame()
        df_set = pd.DataFrame()
        if selection['tech']['name']:
            for i, tech in enumerate(selection['tech']['name']):
                param = selection['tech']['parameters'][i]
                if tech == 'all_tech':
                    sel = self.__bibdata.get_data()
                else:
                    sel = self.__bibdata.get_data(entry=tech)
                if param == 'all':
                    sel_by_param = sel
                else:
                    sel_by_param = pd.concat([self.__bibdata.filter_by_param(sel, par) for par in param])
                df_tech = pd.concat([df_tech, sel_by_param])
        if selection['tech']:
            for st in selection['sets']:
                sel = self.__bibdata.get_data(set_name=st)
                df_set = pd.concat([df_set, sel])
        if df_set.empty and df_tech.empty:
            df = self.__bibdata.get_data()
        elif df_tech.empty:
            df = df_set
        elif df_set.empty:
            df = df_tech
        else:
            df = pd.merge(df_tech, df_set, left_index=True, right_index=True, how='inner')
            df = keep_reference_df(df)
       
        return df

    def __read_title(self, title):
        arguments = re.findall(r'\[(.*?)\]', title)
        arguments = ",".join(arguments).lower()
        
        title = re.sub(r'\[(.*?)\]', '', title)
        elements = re.split(r'\s+(?![^()]*\))', title)
        
        functionality = elements[0]
        df = self.__bibdata.get_data()
        valid_technologies = [tech.lower() for tech in df['entry'].unique()]
        valid_sets = [set for set in list(set(df['sets'])) if set != '']

        selection = {'tech': {'name': [], 'parameters': []}, 'sets': []}
        for el in elements[1:]:
            param = []
            keep = False
            remove = False
            if el == "":
                continue
            if el[-1] == '*':
                el = el[:-1]
                keep = True
            elif el[-1] == '-':
                remove = True
                el = el[:-1]
            if len(el.split("(")) > 1:
                param = re.findall(r'\((.*?)\)', el)[0]
                param = [par.strip() for par in param.split(",")]
                el = el.split("(")[0]
                if el == '':
                    el = 'all_tech'
            if el.lower() in valid_technologies or el == 'all_tech':
                if keep:
                    self.__selected_data['tech']['name'].append(el)
                    if param:
                        self.__selected_data['tech']['parameters'].append(param)
                    else:
                        self.__selected_data['tech']['parameters'].append('all')
                elif remove:
                    try:
                        ind = self.__selected_data['tech']['name'].index(el)
                        del self.__selected_data['tech']['name'][ind]
                        del self.__selected_data['tech']['parameters'][ind]
                    except IndexError:
                        print(el + " is already not part of selection")
                else:
                    selection['tech']['name'].append(el)
                    if param:
                        selection['tech']['parameters'].append(param)
                    else:
                        selection['tech']['parameters'].append('all')
            elif el in valid_sets:
                if keep:
                    self.__selected_data['sets'].append(el)
                elif remove:
                    self.__selected_data['sets'].remove(el)
                else:
                    selection['sets'].append(el)

        if "histogram" not in functionality.lower():
            [selection['tech']['name'].append(tech) for tech in self.__selected_data['tech']['name']]
            [selection['tech']['parameters'].append(tech) for tech in self.__selected_data['tech']['parameters']]
            [selection['sets'].append(sets) for sets in self.__selected_data['sets']]

        return functionality, arguments, selection

    @staticmethod
    def convert_json_to_r(py_json):
        fig_json = re.sub("\[", "list(", py_json)
        fig_json = re.sub("\]", ")\n", fig_json)
        fig_json = re.sub("\{", "list(", fig_json)
        fig_json = re.sub("\}", ")\n", fig_json)
        fig_json = re.sub(":", " = ", fig_json)
        fig_json = re.sub("true", "TRUE", fig_json)

        return fig_json


class Chunk:
    def __init__(self, code):
        self.manager = None
        self.display = False
        self.content = None
        self.title = None
        self.manager, self.display, self.content, self.title = self.read_code(code)

    @staticmethod
    def read_code(code):
        if isinstance(code, list):
            lines = code
        elif isinstance(code, str):
            lines = code.split("\n")
        else:
            raise TypeError("The code provided by the chunk is not in an expected format")
        manager = lines[0][0]
        display = False
        content = '\n '.join(lines[1:])
        if manager == ':':
            display = True
        if manager == ':' or manager == '!':
            title = lines[0][1:].strip()
        elif manager == '#':
            title = None
        else:
            raise 'Manager is not valid, did you forget to put one?'
        return manager, display, content, title

