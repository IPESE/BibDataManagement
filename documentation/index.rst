BibData
++++++++
.. to build :
..      cd documentation
..      make html

.. figure:: images/biblio.jpg
   :width: 80%

.. card::

    BibData is a tool developed to centralise the references and the use of data such as model parameters.

    The idea is to collect and retrieve values across a bibliography, that can be shared among various users. The idea is to use the
    **Notes** option in bibliography manager softwares. The two that have been tested as compatible are **Zotero** and **Mendeley**.

    The package then provides an easy way to extract custom data set in the *annote* or *note* field of a bib file,
    and can be used in Python or in Quarto, using ``rbibdata`` chunk.


The basics
==============================

The package is designed to extract data in a specific format in the notes field of the .bib file.
Each position in the note has a meaning, according to the following format:

::

    +- ENTRY # row_key:set: general description of entry # confidence = 0.4 # ref_year = 1975
    param1 = min:value1:max [unit1] # short_name: a comment about the param and its value
    param2 = value2 [unit2] # # confidence = 0.4
    +- /ENTRY

Where the fields described as follows:

+------------------------+-------------------------------------------+------------+
| Fields                 | Description                               | Mandatory  |
+========================+===========================================+============+
| ENTRY                  | The name of the entry to which the        | True       |
|                        | parameters belong                         |            |
+------------------------+-------------------------------------------+------------+
| row_key                | An identifier                             | False      |
+------------------------+-------------------------------------------+------------+
| set                    | Use to retrieve all values from a user    | False      |
|                        | (e.g. all values for *scenario_oil*)      |            |
+------------------------+-------------------------------------------+------------+
| general_description    | A comment on the entry or on the paper    | False      |
+------------------------+-------------------------------------------+------------+
| param                  | Name of the parameter characterised       | False      |
+------------------------+-------------------------------------------+------------+
| value                  | Value of the parameter                    | True       |
+------------------------+-------------------------------------------+------------+
| min                    | Minimal value that the parameter can      | False      |
|                        | have                                      |            |
+------------------------+-------------------------------------------+------------+
| max                    | Maximal value that the parameter can      | False      |
|                        | have                                      |            |
+------------------------+-------------------------------------------+------------+
| unit                   | Unit of the parameter                     | True       |
+------------------------+-------------------------------------------+------------+
| confidence             | The level of confidence in the value      | False      |
|                        | (useful for average). Can be precised     |            |
|                        | for a technology or a parameter. The      |            |
|                        | value from the parameter overwrites the   |            |
|                        | one from the technology                   |            |
+------------------------+-------------------------------------------+------------+
| ref_year               | The reference year for the values, in     | False      |
|                        | case they have to be actualised. If not   |            |
|                        | precised, the publication date is used    |            |
+------------------------+-------------------------------------------+------------+

The minimal information to provide is the ``+- ENTRY   +- /ENTRY``. The fields after the # are optional, as well as
the min and max values.

.. note::
    Spaces in the key/value line are for readability but are not required.

To be able to read all those notes at once, one must export the bibliography collection, either in *Better BibTeX* or in *BibTeX*. In the last case,
the line breaks one must be added directly in the note as such:

::

    +- ENTRY # row_key:set: general description of tech # confidence = 0.4 \n
    param1 = min:value1:max [unit1] # short_name: a comment about the param and its value \n
    param2 = value2 [unit2] # # confidence = 0.4 \n
    +- /ENTRY


Additional format
=================

For some models, such as _Energyscope_, one needs to add also values for layers.
In that case, the keyword layer should be added in the parameter field.
Again, spaces are for readility and special characters can be added without hindering the parsing.

::

    +- TECH # row_key:set: general description of tech # confidence = 0.4 # ref_year = 1975
    Layer: param1 = min:value1:max [unit1] # short_name: a comment about the param and its value
    layer_param2 = value2 [unit2] # # confidence = 0.4
    +- /TECH


**Energyscope** also has demands and resources. Of course, they can also be reported using the package, following this format for a proper export of the data.

* Demands

  .. code-block:: r

      +- DEMAND % SECTOR # row_key:set: general description of tech # confidence = 0.4 # ref_year = 1975
      end_use_category1 = min:value1:max [unit1] # short_name: a comment about the param and its value
      end_use_category2 = value2 [unit2] # # confidence = 0.4
      +- /SECTOR


  For instance:

  .. code-block:: r

      +- DEMAND % INDUSTRY
      ELECTRICITY_MV = 30 [GWh]
      HEAT_HIGH_T = 60 [GWh]
      +- /INDUSTRY

* Resources

  .. code-block:: r

      +- RESOURCE % RESOURCE # row_key:set: general description of tech # confidence = 0.4 # ref_year = 1975
      param1 = min:value1:max [unit1] # short_name: a comment about the param and its value
      param2 = value2 [unit2] # # confidence = 0.4
      +- /RESOURCE


  For instance:

  .. code-block:: r

      +- RESOURCE % BIOGAS
      c_op = 20 [USD/GWh]
      +-/BIOGAS


To help to format properly the note, an interface has been developed that connects to Zotero and writes the note with the correct formatting.
The interface is not online but can be found on Git `bibdatamanagement_ui <https://gitlab.epfl.ch/ipese/bibdatamanagement/bibdatamanagement_ui>`_ and run locally.
This interface is related to EnergyScope but could be adapted to any type of note.


Use the data in code
=======================

With the data correctly referenced in a bibliography, in their notes, with the formatting above, the *.bib* file
must be exported and read in code.

.. grid::

    .. grid-item-card:: :fab:`python` For Python users
        :link: sections/BibDataManagement.html

        Describes the Python package.

    .. grid-item-card:: :material-regular:`summarize` For Quarto users
        :link: sections/RBibData.html

        Describes the R library, useful for reporting.

.. toctree::
   :maxdepth: 1
   :hidden:

   sections/BibDataManagement
   sections/RBibData


Contribute
==========

All contributions are welcome in this project. The users may find some additional features are needed and propose
or even implement them.

All suggestions or implementation must be tracked with dedicated issues and reported at the
`project GitHub <https://github.com/IPESE/BibDataManagement/issues>`_

