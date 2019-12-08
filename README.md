# Moka Panel App (mokapapp)

`mokapapp` imports Panel App panels into the Viapath Genetics LIMS system (Moka). Simply [install](#installation), create a [configuration file](#configuration-file) and run:

```bash
$ mokapapp-import -c config.ini
```

`mokapapp` beings by deactivating deprecated PanelApp panels in Moka, indicated by their absence from the API.

Moka requires a unique hash for each panel's green and amber gene lists. `mokapapp` builds these hashes from the PanelApp API response as MokaPanel objects. Three checks are performed on each MokaPanel before importing:

* Are all panel hashes in dbo.Item?
* Are all panel versions in dbo.Item?
* Are all panel HGNC IDs in dbo.GenesHGNC_Current?

Note that new hashes and versions are inserted into the Item table, but `mokapapp` will raise an error if the HGNC check fails as GenesHGNC_Current must be updated manually.

## Installation

Clone this repository and install with `pip` (tested on a Linux OS with python v3.6.5):

```
$ git clone https://github.com/moka-guys/mokapapp.git
$ pip install ./mokapapp
```

## Usage

```
usage: mokapapp-import [-h] [-c CONFIG] [--logfile LOGFILE]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        A mokapapp config.ini file
  --logfile LOGFILE     A file to write application log outputs
```

## Configuration file

`mokapapp-import` requires a `config.ini` file with Moka database connection details:

```bash
# Example config.ini
[mokadb]
server = 10.10.10.10
db = dbname
user = username
password = password
```

## Testing

Unit tests in the `tests/` directory are run using `pytest`. An *auth.py* file containing test server details must be present in  `tests/`:
```python
# Example auth.py
SV_TE_MOKDBS01 = {
    'server': '10.10.10.100',
    'db': 'database',
    'user': 'username',
    'password': 'password'
}
```

Once this file has been created run all tests:
> $ pytest .

## Notes

* Panel App gene confidence levels are converted to Green, Amber and Red colours as specified in Appendix A p.29 of the [Panel App Handbook v5.5](https://panelapp.genomicsengland.co.uk/media/files/PanelAppHandbookVersion55.pdf).

## License

MIT License © 2019 Viapath Genome Informatics
