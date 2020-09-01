# Moka Panel App (mokapapp)

`mokapapp` imports Panel App panels into the Viapath Genetics LIMS system (Moka).

```bash
$ git clone https://www.github.com/moka-guys/mokapapp.git
$ pip install ./mokapapp
$ mokapapp -c config.ini
```

## Overview

`mokapapp` queries the PanelApp API, checks that Moka contains the required import keys and then imports new panels or deactives depreciated panels.

Moka splits PanelApp panels based on gene colour. `mokapapp` builds these split panels from the PanelApp API response as MokaPanel objects. Three checks are performed on each MokaPanel before importing:

* Are all panel hashes in dbo.Item?
* Are all panel versions in dbo.Item?
* Are all panel HGNC IDs in dbo.GenesHGNC_Current?

Note that new hashes and versions are inserted into the Item table, but `mokapapp` will raise an error if the HGNC check fails as GenesHGNC_Current must be updated manually.

A logfile is produced which ends by summarising counts of panels downloaded, imported and deactivated by running `mokapapp`.


## Installation

Clone this repository and install with `pip` (tested on a Linux OS with python v3.6.5):

```
$ git clone https://github.com/moka-guys/mokapapp.git
$ pip install ./mokapapp
```

Warning: When working on the Trust server, ensure the http proxy is accurate, otherwise no requests can be made:
```
# Example of how to set proxy environment variables
pproxy="http://CORRECT_PROXY_URL:CORRECT_PROXY_PORT"
export HTTP_PROXY=$pproxy
export http_proxy=$pproxy
export HTTPS_PROXY=$pproxy
export https_proxy=$pproxy
```

## Usage

```
usage: mokapapp-import [-h] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        A mokapapp config.ini file
```

## config.ini file

`mokapapp` requires a `config.ini` file with Moka database connection details:

```bash
[mokapapp]
logdir = .  # Log directory
db = mokadb_prod  # Database defined in later config category to use
min_panel_count = 500 # Minimum number of panels that should be generated from API response

[endpoints] # Required PanelApp endpoints
panels = https://panelapp.genomicsengland.co.uk/api/v1/panels
signed_off_panels = https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff

[mokadb_prod] # Moka database connection details
server = 99.999.999.999
db = DATABASE
user = USERNAME
password = PASSWORD

[mokadb_test] # Test database connection details (for testing)
server = 99.999.999.999
db = DATABASE
user = USERNAME
password = PASSWORD
```

## Logfiles

Outputs a logfile to the directory passed to `--logdir` flag. If no directory is given, logfiles are written to the current location. Mokapp logs actions performed for each panel, ending with a report summarising the following:
* Panels retrieved from the PanelApp API and MokaPanels objects created
* Panels depreciated in PanelApp and thus deactivated in Moka
* New panel name items and versions inserted into Moka
* New MokaPanels inserted into Moka
* A string to indicate successful completion: "mokapapp.app: INFO - Moka Panel import complete"

## Testing

Unit tests in the `tests/` directory are run using `pytest`. You can use the conda environment.yml file to ensure the same development environment.

Tests must be run against the test database by passing a mokapapp config file with a [mokadb_test] entry:
> $ pytest ./mokapapp/tests -c config.ini


## Notes

* Panel App gene confidence levels are converted to Green, Amber and Red colours as specified in Appendix A p.29 of the [Panel App Handbook v5.5](https://panelapp.genomicsengland.co.uk/media/files/PanelAppHandbookVersion55.pdf).

## License

MIT License © 2020 Viapath Genome Informatics
