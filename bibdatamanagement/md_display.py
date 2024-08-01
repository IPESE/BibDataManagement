from pylatexenc.latex2text import LatexNodes2Text
from .bibdatamanagement_es import BibDataManagementES  # Adjust import based on actual package structure


class MdDisplay:
    """
    MdDisplay class provides utility methods to convert LaTeX to text
    and generate Markdown formatted dataframes from BibTeX entries.

    Methods
    -------
    latex_to_text(item):
        Converts LaTeX formatted strings or lists of strings to plain text.
    
    print_md_params(bib_file_path, filter_entry):
        Loads BibTeX data, filters it based on an entry, converts LaTeX fields to text,
        and returns a Markdown formatted dataframe with the parameters.

    print_md_sources(bib_file_path, filter_entry):
        Loads BibTeX data, filters it based on an entry, converts LaTeX fields to text,
        and returns a Markdown formatted dataframe with the data sources.
    """

    @staticmethod
    def latex_to_text(item):
        """
        Converts LaTeX formatted strings or lists of strings to plain text.

        Parameters
        ----------
        item : str or list of str
            The LaTeX formatted string or list of strings to be converted.

        Returns
        -------
        str or list of str
            The plain text string or list of plain text strings.
        """
        LN2T = LatexNodes2Text()
        if isinstance(item, str):
            return LN2T.latex_to_text(item)
        elif isinstance(item, list):
            return [LN2T.latex_to_text(elem) if isinstance(elem, str) else elem for elem in item]
        else:
            return item

    @staticmethod
    def print_md_params(bib_file_path, filter_entry, category_entry=None):
        """
        Loads BibTeX data from file, filters it based on an entry, converts LaTeX fields to text,
        and returns a Markdown formatted dataframe with the parameters.

        Parameters
        ----------
        bib_file_path : str
            The file path to the BibTeX file.
        filter_entry : str
            The entry to filter the BibTeX data by.

        Returns
        -------
        str
            A Markdown formatted dataframe with the parameters.
        """
        # Load BibTeX data from file
        bibdata = BibDataManagementES(bib_file_path)
        if not category_entry:
            df_bib = bibdata.get_data(entry="", category_name="")
        else:
            df_bib = bibdata.get_data(entry="", category_name=category_entry)

        # Filter the DataFrame for specific entry
        df_filtered = df_bib[df_bib["entry"] == filter_entry].reset_index(drop=True)

        # Apply LaTeX to text conversion to the 'title' and 'author' columns
        df_filtered['title'] = df_filtered['title'].apply(MdDisplay.latex_to_text)
        df_filtered['author'] = df_filtered['author'].apply(MdDisplay.latex_to_text)
        df_filtered['journal'] = df_filtered['journal'].apply(MdDisplay.latex_to_text)

        # Create the 'source_reference' column
        df_filtered["source_reference"] = df_filtered.apply(
            lambda row: f"{'; '.join(row['author'])}, ({row['year']}): \"[{row['title']}]({row['howpublished']})\"" 
            if row['howpublished'].strip() 
            else f"{'; '.join(row['author'])}, ({row['year']}): \"{row['title']}\"", 
            axis=1
        )

        # Prepare DataFrame for display
        df_display = df_filtered[["entry_key", "value", "unit", "sets", "source_reference"]]
        df_display = df_display.sort_values(["entry_key", "value"]).reset_index(drop=True).set_index("entry_key")

        # Return DataFrame as Markdown
        return df_display.to_markdown()

    @staticmethod
    def print_md_sources(bib_file_path, filter_entry):
        """
        Loads BibTeX data from file, filters it based on an entry, converts LaTeX fields to text,
        and returns a Markdown formatted dataframe with the data sources.

        Parameters
        ----------
        bib_file_path : str
            The file path to the BibTeX file.
        filter_entry : str
            The entry to filter the BibTeX data by.

        Returns
        -------
        str
            A Markdown formatted dataframe with the data sources.
        """
        # Load BibTeX data from file
        bibdata = BibDataManagementES(bib_file_path)
        df_bib = bibdata.get_data(entry="", category_name="")

        # Filter the DataFrame for specific entry
        df_filtered = df_bib[df_bib["entry"] == filter_entry].reset_index(drop=True)

        # Apply LaTeX to text conversion to the 'title' and 'author' columns
        df_filtered['title'] = df_filtered['title'].apply(MdDisplay.latex_to_text)
        df_filtered['author'] = df_filtered['author'].apply(MdDisplay.latex_to_text)
        df_filtered['journal'] = df_filtered['journal'].apply(MdDisplay.latex_to_text)

        # Create the 'source_reference_long' column with DOIs
        df_filtered["source_reference_long"] = df_filtered.apply(
            lambda row: ". ".join(filter(None, [
                f"{'; '.join(row['author'])}" if row['author'] else None,
                f"({row['year']})" if row['year'].strip() else None,
                f"\"[{row['title']}]({row['howpublished']})\"" if row['howpublished'].strip() else f"\"{row['title']}\"",
                f"{row['journal']}" if row['journal'].strip() else None,
                f"[https://doi.org/{row['doi']}](https://doi.org/{row['doi']})" if row['doi'].strip() else None
            ])),
            axis=1
        )

        # Prepare DataFrame for Data Sources display
        df_sources = df_filtered[["source_reference_long"]].drop_duplicates()
        df_sources = df_sources.rename(columns={"source_reference_long": "Data Sources"})

        # Return DataFrame as Markdown
        return df_sources.to_markdown(index=False)
