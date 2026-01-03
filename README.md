# BFPO Address Scraper & XML Generator

A Python toolkit for scraping British Forces Post Office (BFPO) addresses from official sources and generating a standardised XML configuration file. Automatically extracts current BFPO locations from GOV.UK and FCDO data sources, resolves country codes using ISO 3166-1 standards, and produces schema-validated XML output.

Ideally suited to produce the xml config file which can then be further used as a reference data lookup of a full BFPO address to be used as part of a wider ISO 20022 structured address solution.  See my other repos for strucutred address projects.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### 🌍 Comprehensive BFPO Data Coverage
- **~165 GOV.UK locations**: Military bases, ships, operations, exercises, naval parties
- **~250 FCDO diplomatic posts**: Embassies, high commissions, consulates worldwide
- **33 isolated detachments**: BFPO 105 box numbers in Germany
- **Total: ~415+ BFPO addresses**

### 🔍 Data Sources
- **GOV.UK Official BFPO Locations**: https://www.gov.uk/guidance/bfpo-locations
- **FCDO Diplomatic Posts**: OpenDocument Spreadsheet (ODS) from GOV.UK
- **Automatic Updates**: Re-scrape to get latest BFPO changes

### 📋 Address Components Extracted
- BFPO numbers with "BFPO" prefix standardisation
- Box numbers for isolated detachments
- Locations and unit names
- BF1 postcodes
- Country names
- ISO 3166-1 alpha-2 country codes (via pycountry)
- Type classification (static, ship, fcdo, operation, exercise, navalparty, detachment)

### 📊 XML Configuration Output
- Schema-validated XML (XSD provided)
- Pretty-formatted with proper indentation
- Sorted by BFPO number
- Country code statistics
- Ready for integration with lookup systems

## Installation

### Requirements
- Python 3.12+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Clone Repository

```bash
git clone https://github.com/domdigby/bfpo-scraper.git
cd bfpo-scraper
```

## Quick Start

### 1. Basic Usage (GOV.UK Only)

```python
from main import BFPOScraperSimple

# Scrape GOV.UK data
scraper = BFPOScraperSimple(output_file="bfpo_config.xml")
scraper.run()
```

**Output**: `bfpo_config.xml` with ~165 BFPO addresses

### 2. Include FCDO Diplomatic Posts

```bash
# Download FCDO ODS file
wget "https://assets.publishing.service.gov.uk/media/5f3f87ae8fa8f5371bb55f64/20200820-Foreign__Commonwealth_and_Development_Office_BFPO_Indicator_List_v2.ods" -O fcdo_bfpo_list.ods

# Run scraper with FCDO data
python main.py fcdo_bfpo_list.ods
```

**Output**: `bfpo_config.xml` with ~415 BFPO addresses

### 3. Command Line Usage

```bash
# Basic usage (GOV.UK only)
python main.py

# With FCDO data
python main.py fcdo_bfpo_list.ods
```

## XML Output Format

```xml
<?xml version="1.0" encoding="utf-8"?>
<Config>
    <!--
    BFPO Address Configuration
    Generated from GOV.UK BFPO locations
    Last Updated: 2026-01-03
    Created By: Affinis Ltd (Dominic Digby)
    Schema: bfpo_config.xsd
    Country Codes: ISO 3166-1 alpha-2 (via pycountry)
    -->
    
    <BFFO_Address>
        <BfpoNum>BFPO 58</BfpoNum>
        <Loc>Dhekelia</Loc>
        <PstCd>BF1 2AU</PstCd>
        <Ctry>Cyprus</Ctry>
        <CtryCd>CY</CtryCd>
        <Type>static</Type>
    </BFFO_Address>
    
    <BFFO_Address>
        <BfpoNum>BFPO 105</BfpoNum>
        <BoxNum>589</BoxNum>
        <Loc>ATC Oberstdorf</Loc>
        <PstCd>BF1 0AX</PstCd>
        <Ctry>Germany</Ctry>
        <CtryCd>DE</CtryCd>
        <Type>detachment</Type>
    </BFFO_Address>
</Config>
```

## BFPO Address Types

| Type | Description | Count (approx) | Example |
|------|-------------|----------------|---------|
| `static` | Permanent military bases | ~30 | BFPO 58 (Dhekelia, Cyprus) |
| `ship` | Royal Navy vessels | ~80 | BFPO 365 (HMS Queen Elizabeth) |
| `fcdo` | Diplomatic posts | ~250 | BFPO 3 (British Embassy Ankara) |
| `operation` | Active military operations | ~50 | BFPO 550 (OP SHADER) |
| `exercise` | Temporary exercises | ~10 | BFPO 510 (Ex Clockwork) |
| `navalparty` | Shore-based naval units | ~5 | BFPO 485 (Diego Garcia) |
| `detachment` | Isolated detachments | 33 | BFPO 105 Box 589 (ATC Oberstdorf) |

## Key Features

### Country Code Resolution

Uses `pycountry` library for ISO 3166-1 alpha-2 codes with intelligent fallbacks:

```python
from main import CountryCodeResolver

code = CountryCodeResolver.get_country_code("Germany")  # → DE
code = CountryCodeResolver.get_country_code("Turkey")   # → TR (handles Türkiye)
code = CountryCodeResolver.get_country_code("USA")      # → US
```

**Special Cases**: Turkey, Holland, USA, Falklands, Ascension, and more

## Use Cases

- **Generate BFPO database** for address lookup systems
- **Keep data current** by re-scraping periodically
- **Analyze BFPO distribution** by country/type
- **Export standardised data** for geocoding/parsing systems
- **Integrate with postal systems** via standardised XML


## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Data Sources

- **GOV.UK BFPO Locations** (Open Government Licence v3.0)
- **FCDO BFPO Indicator List**
- **Country Codes** via [pycountry](https://pypi.org/project/pycountry/)

## License

MIT License - see [LICENSE](LICENSE)

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/domdigby/bfpo-scraper/issues)
- 📧 **Contact**: info@affinis.co.uk

---

**Status**: Production Ready ✅