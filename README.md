# Bibliography management

The goal is to provide an easy way to extract in python custom data set in the *annote* field of a bib file.

## Installation

**BibdataManagement** library is stored in IPESE pypi server located on https://ipese-internal.epfl.ch/registry/pypi. and https://pypi.org/project/bibdatamanagement/

To include the library in your projects, do the following in _requirements.txt_:
1. Include the package 
```
bibdatamanagement >= 0.6.0
```

Otherwise, the package can be installed by using a _pip_ command.  
```
pip install bibdatamanagement
```

## Data format

The package is designed to extract data in a specific format. The initial development was made for technologies parameter
used to model it.
```
+- ENTRY # row_key:set: general description of tech
param1 = min:value1:max [unit1] # short_name: a comment about the param and its value
param2 = value2 [unit2]
+- /ENTRY
```
Where the fields described as follows:
|Fields | Description | Mandatory|
|--- | --- | ---|
|ENTRY | The name of the tech to which the parameters belong | True|
|row_key | An identifier | False|
|set | Use to retrieve all values from a user (e.g. all values for   *scenario_oil*) | False|
|general_description | A comment on the tech or on the paper | False|
|param | Name of the parameter characterised | False|
|value | Value of the parameter | True|
|min | Minimal value that the parameter can have | False|
|max | Maximal value that the parameter can have | False|
|unit | Unit of the parameter | True|

The minimal information to provide is the `+- ENTRY       +- /ENTRY`. The fields after the _#_ are optional, as well as
the min and max values.

> Nb: spaces in the key/value line are for readability but are not required

## Usage

The minimal workflow to access the data in the _.bib_ is the following.

```python
from bibdata_management.bibdata_management import BibDataManagement
bib_file = 'your_path/your_file.bib'
bibdata = BibDataManagement(bib_file)
df_bib = bibdata.get_data(tech_name='YOUR_ENTRY', set_name='YOUR_SET')
```

One can also add a _.csv_ file that contains the default value for parameters description (short name, long name, description).
```{python}
bibdata = BibDataManagement(bib_file, 'your_default_file.csv')
```

## Documentation

More information on the fields and the methods is available in the [documentation website](https://ipese-web.epfl.ch/static/docs/bibdatamanagement/index.html)

## Suggestions and contributions

All suggestions or implementation must be tracked with dedicated issues and reported at the [project GitLab](https://gitlab.epfl.ch/ipese/bibdatamanagement/bibdata-package/issues) 

If you want to make the format evolve or implement a new python function, create an issue before anything else.

## Author

- [Joseph Loustau](mailto:joseph.loustau@gmail.com), IPESE