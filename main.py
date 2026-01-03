#!/usr/bin/env python3
"""
BFPO Data Scraper and XML Generator (Simplified Schema with pycountry)

Scrapes BFPO address data from GOV.UK and generates XML following the provided XSD schema.

Schema: Simple flat structure with BFFO_Address elements
Fields: BfpoNum, Loc, PstCd, Ctry, CtryCd, Type

Dependencies:
    pip install requests beautifulsoup4 lxml pandas odfpy pycountry --break-system-packages

Usage:
    python bfpo_scraper_simple.py
"""
import os
import sys
import traceback
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
import pandas as pd
import requests
import pycountry


class CountryCodeResolver:
    """Resolve country names to ISO 3166-1 alpha-2 codes using pycountry."""

    # Special cases and common variations not handled by pycountry
    SPECIAL_CASES = {
        'Holland': 'NL',  # Netherlands
        'USA': 'US',  # United States
        'Turkey': 'TR',  # Turkey (official name changed to Türkiye in 2022)
        'Falklands': 'FK',  # Falkland Islands
        'Ascension': 'AC',  # Ascension Island (user-assigned code)
        'British Indian Ocean Territory': 'IO',
        'Africa': 'AF',  # Generic Africa (for operations without specific country)
    }

    @staticmethod
    def get_country_code(country_name: str) -> Optional[str]:
        """
        Get ISO 3166-1 alpha-2 country code from country name.
        
        Args:
            country_name: Country name (e.g., "Germany", "United Kingdom")
        
        Returns:
            2-character country code or None if not found
        """
        if not country_name:
            return None

        # Check special cases first
        if country_name in CountryCodeResolver.SPECIAL_CASES:
            return CountryCodeResolver.SPECIAL_CASES[country_name]

        # Try exact match by name
        try:
            country = pycountry.countries.get(name=country_name)
            if country:
                return country.alpha_2
        except (KeyError, AttributeError):
            pass

        # Try fuzzy search (case-insensitive)
        try:
            countries = pycountry.countries.search_fuzzy(country_name)
            if countries:
                return countries[0].alpha_2
        except LookupError:
            pass

        # Try common name variations
        name_variations = [
            country_name.upper(),
            country_name.lower(),
            country_name.title(),
        ]

        for variation in name_variations:
            try:
                country = pycountry.countries.get(common_name=variation)
                if country:
                    return country.alpha_2
            except (KeyError, AttributeError):
                pass

        # Log warning for unmapped countries
        print(f"  Warning: Could not map country '{country_name}' to ISO code")
        return None

    @staticmethod
    def validate_country_code(code: str) -> bool:
        """
        Validate that a country code exists in ISO 3166-1.
        
        Args:
            code: 2-character country code
        
        Returns:
            True if valid
        """
        if not code or len(code) != 2:
            return False

        # Check special cases
        if code in CountryCodeResolver.SPECIAL_CASES.values():
            return True

        try:
            pycountry.countries.get(alpha_2=code.upper())
            return True
        except (KeyError, AttributeError):
            return False


class BFPOScraperSimple:
    """Scrape BFPO data from GOV.UK and generate XML following simplified schema."""

    GOV_UK_BFPO_URL = "https://www.gov.uk/bfpo/find-a-bfpo-number"
    FCDO_ODS_URL = "https://assets.publishing.service.gov.uk/media/5f3f87ae8fa8f5371bb55f64/20200820-Foreign__Commonwealth_and_Development_Office_BFPO_Indicator_List_v2.ods"

    def __init__(self, output_file: str = "bfpo_config.xml", fcdo_ods_file: Optional[str] = None):
        self.output_file = output_file
        self.fcdo_ods_file = fcdo_ods_file  # Optional pre-downloaded ODS file
        self.addresses = []  # List of BFPO addresses
        self.country_resolver = CountryCodeResolver()

    def scrape_gov_uk_bfpo(self) -> None:
        """Scrape BFPO locations from GOV.UK HTML page and FCO"""
        print("\nScraping GOV.UK BFPO locations...")

        try:
            response = requests.get(self.GOV_UK_BFPO_URL, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse each section
            self._parse_germany_locations(soup)
            self._parse_uk_locations(soup)
            self._parse_europe_locations(soup)
            self._parse_world_locations(soup)
            self._parse_ships(soup)
            self._parse_naval_parties(soup)
            self._parse_operations(soup)
            self._parse_exercises(soup)
            self._parse_isolated_detachments(soup)

            print(f"✓ Scraped {len(self.addresses)} BFPO addresses from GOV.UK")

        except Exception as e:
            print(f"✗ Error scraping GOV.UK: {e}")
            raise

    def _parse_table_rows(self, table) -> list[list[str]]:
        """Extract rows from HTML table."""
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        return rows

    def _add_address(self, bfpo_num: str, location: str, postcode: Optional[str] = None,
                     country: Optional[str] = None, bfpo_type: str = 'static',
                     box_num: Optional[str] = None) -> None:
        """Add BFPO address to list with country code resolution."""
        # Ensure BfpoNum is prefixed with "BFPO "
        if not bfpo_num.upper().startswith('BFPO'):
            bfpo_num = f'BFPO {bfpo_num}'

        address = {
            'BfpoNum': bfpo_num,
            'Loc': location,
            'Type': bfpo_type
        }

        if box_num:
            address['BoxNum'] = box_num

        if postcode:
            address['PstCd'] = postcode

        if country:
            address['Ctry'] = country
            country_code = self.country_resolver.get_country_code(country)
            if country_code:
                address['CtryCd'] = country_code

        self.addresses.append(address)

    def _parse_germany_locations(self, soup) -> None:
        """Parse Germany BFPO locations."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='germany-bfpo-locations')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Germany' in s and 'BFPO' in s)
        if not heading:
            print("  Warning: Could not find Germany BFPO locations section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                self._add_address(row[1], row[0], row[2], 'Germany', 'static')

    def _parse_uk_locations(self, soup) -> None:
        """Parse UK BFPO locations."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='uk-bfpo-locations')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'UK' in s and 'BFPO' in s)
        if not heading:
            print("  Warning: Could not find UK BFPO locations section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                self._add_address(row[1], row[0], row[2], 'United Kingdom', 'static')

    def _parse_europe_locations(self, soup) -> None:
        """Parse Europe BFPO locations."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='rest-of-europe-bfpo-locations')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Rest of Europe' in s)
        if not heading:
            print("  Warning: Could not find Europe BFPO locations section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 4:
                self._add_address(row[1], row[0], row[2], row[3], 'static')

    def _parse_world_locations(self, soup) -> None:
        """Parse rest of world BFPO locations."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='rest-of-the-world-bfpo-locations')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Rest of the world' in s)
        if not heading:
            print("  Warning: Could not find World BFPO locations section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 4:
                self._add_address(row[1], row[0], row[2], row[3], 'static')

    def _parse_ships(self, soup) -> None:
        """Parse HM Ships."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='hm-ships')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'HM Ships' in s)
        if not heading:
            print("  Warning: Could not find HM Ships section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                self._add_address(row[1], row[0], row[2], None, 'ship')

    def _parse_naval_parties(self, soup) -> None:
        """Parse Naval parties."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='naval-parties')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Naval parties' in s)
        if not heading:
            print("  Warning: Could not find Naval parties section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                # Naval parties often have location in first column
                country = None
                location = row[0]

                # Try to extract country from location string
                # Common patterns: "Location NPxxxx", "City NPxxxx"
                if 'Diego Garcia' in location:
                    country = 'British Indian Ocean Territory'
                elif 'Ottawa' in location:
                    country = 'Canada'
                elif 'Singapore' in location:
                    country = 'Singapore'
                elif 'Den Helder' in location:
                    country = 'Netherlands'
                elif 'Falklands' in location:
                    country = 'Falklands'

                self._add_address(row[1], location, row[2], country, 'navalparty')

    def _parse_operations(self, soup) -> None:
        """Parse Operations."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='operations')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Operations' in s)
        if not heading:
            print("  Warning: Could not find Operations section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                self._add_address(row[1], row[0], row[2], None, 'operation')

    def _parse_exercises(self, soup) -> None:
        """Parse Exercises."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h2', id='exercises')
        if not heading:
            # Fallback to text search
            heading = soup.find('h2', string=lambda s: s and 'Exercises' in s)
        if not heading:
            print("  Warning: Could not find Exercises section")
            return

        table = heading.find_next('table')
        if not table:
            return

        for row in self._parse_table_rows(table):
            if len(row) >= 3:
                self._add_address(row[1], row[0], row[2], None, 'exercise')

    def _parse_isolated_detachments(self, soup) -> None:
        """Parse isolated detachments in Germany (BFPO 105 box numbers)."""
        # Use id attribute which is more reliable than text matching
        heading = soup.find('h3', id='isolated-detachments-box-numbers')
        if not heading:
            # Fallback to text search
            heading = soup.find('h3', string=lambda s: s and 'Isolated detachments' in s)
        if not heading:
            print("  Warning: Could not find Isolated detachments section")
            return

        table = heading.find_next('table')
        if not table:
            return

        # Table structure: Location | Box number
        ISOLATED_DETACHMENT_POSTCODE = 'BF1 0AX'

        for row in self._parse_table_rows(table):
            if len(row) >= 2:
                location = row[0]
                box_num = row[1]

                # All isolated detachments are under BFPO 105 in Germany
                self._add_address(
                    '105',
                    location,
                    ISOLATED_DETACHMENT_POSTCODE,
                    'Germany',
                    'detachment',
                    box_num=box_num
                    )

    def download_fcdo_ods(self) -> Optional[str]:
        """Download FCDO ODS file to temporary location."""

        print("\nDownloading FCDO ODS file...")

        try:
            response = requests.get(self.FCDO_ODS_URL, timeout=30)
            response.raise_for_status()

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ods')
            temp_file.write(response.content)
            temp_file.close()

            print(f"✓ Downloaded FCDO ODS file: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            print(f"✗ Error downloading FCDO ODS: {e}")
            return None

    def parse_fcdo_ods(self, ods_file: str) -> None:
        """Parse FCDO ODS spreadsheet with multi-column layout."""
        print(f"\nParsing FCDO ODS file: {ods_file}")

        try:
            df = pd.read_excel(ods_file, engine='odf')
            print(f"✓ Loaded FCDO spreadsheet with {len(df)} rows")

            # The FCDO file has a multi-column layout:
            # Location, BFPO No, Postcode, [empty], Location.1, BFPO No.1, Postcode.1, [empty], etc.
            # Data is arranged horizontally in groups of 3 columns

            # Identify column groups
            column_groups = []

            # First group (no suffix)
            if 'Location' in df.columns and 'BFPO No' in df.columns and 'Postcode' in df.columns:
                column_groups.append(('Location', 'BFPO No', 'Postcode'))

            # Numbered groups (Location.1, Location.2, etc.)
            i = 1
            while True:
                loc_col = f'Location.{i}'
                bfpo_col = f'BFPO No.{i}'
                post_col = f'Postcode.{i}'

                if loc_col in df.columns and bfpo_col in df.columns and post_col in df.columns:
                    column_groups.append((loc_col, bfpo_col, post_col))
                    i += 1
                else:
                    break

            print(f"  Found {len(column_groups)} column groups")

            fcdo_count = 0

            # Process each row
            for _, row in df.iterrows():
                # Process each column group
                for loc_col, bfpo_col, post_col in column_groups:
                    try:
                        location = str(row[loc_col]).strip()
                        bfpo_num = str(row[bfpo_col]).strip()
                        postcode = str(row[post_col]).strip()

                        # Skip if any field is NaN or empty
                        if location == 'nan' or location == '' or bfpo_num == 'nan' or bfpo_num == '':
                            continue

                        # Clean up postcode
                        if postcode == 'nan' or postcode == '':
                            postcode = None

                        # Try to infer country from location name
                        country = self._infer_country_from_location(location)

                        # Add address
                        self._add_address(bfpo_num, location, postcode, country, 'fcdo')
                        fcdo_count += 1

                    except Exception as e:
                        # Skip invalid entries in this column group
                        continue

            print(f"✓ Parsed {fcdo_count} FCDO locations")

        except Exception as e:
            print(f"✗ Error parsing FCDO ODS: {e}")
            traceback.print_exc()

    def _infer_country_from_location(self, location: str) -> Optional[str]:
        """
        Infer country name from location string.
        
        FCDO locations typically follow patterns like:
        - "British Embassy Ankara" → Turkey
        - "British High Commission Ottawa" → Canada
        - "British Consulate General New York" → USA
        """
        location_lower = location.lower()

        # Common patterns for inferring country from city/location
        country_patterns = {
            # Europe
            'ankara': 'Turkey',
            'paris': 'France',
            'berlin': 'Germany',
            'madrid': 'Spain',
            'rome': 'Italy',
            'athens': 'Greece',
            'vienna': 'Austria',
            'brussels': 'Belgium',
            'amsterdam': 'Netherlands',
            'dublin': 'Ireland',
            'lisbon': 'Portugal',
            'copenhagen': 'Denmark',
            'stockholm': 'Sweden',
            'oslo': 'Norway',
            'helsinki': 'Finland',
            'warsaw': 'Poland',
            'prague': 'Czech Republic',
            'budapest': 'Hungary',
            'bucharest': 'Romania',
            'sofia': 'Bulgaria',
            'moscow': 'Russia',

            # Americas
            'ottawa': 'Canada',
            'washington': 'USA',
            'new york': 'USA',
            'los angeles': 'USA',
            'san francisco': 'USA',
            'chicago': 'USA',
            'boston': 'USA',
            'atlanta': 'USA',
            'mexico city': 'Mexico',
            'brasilia': 'Brazil',
            'buenos aires': 'Argentina',
            'santiago': 'Chile',
            'lima': 'Peru',
            'bogota': 'Colombia',

            # Asia
            'tokyo': 'Japan',
            'beijing': 'China',
            'shanghai': 'China',
            'seoul': 'South Korea',
            'delhi': 'India',
            'mumbai': 'India',
            'bangkok': 'Thailand',
            'singapore': 'Singapore',
            'jakarta': 'Indonesia',
            'manila': 'Philippines',
            'kuala lumpur': 'Malaysia',
            'hanoi': 'Vietnam',
            'islamabad': 'Pakistan',
            'kabul': 'Afghanistan',
            'tehran': 'Iran',
            'riyadh': 'Saudi Arabia',
            'dubai': 'United Arab Emirates',
            'abu dhabi': 'United Arab Emirates',

            # Oceania
            'canberra': 'Australia',
            'sydney': 'Australia',
            'melbourne': 'Australia',
            'wellington': 'New Zealand',
            'auckland': 'New Zealand',

            # Africa
            'cairo': 'Egypt',
            'nairobi': 'Kenya',
            'johannesburg': 'South Africa',
            'pretoria': 'South Africa',
            'lagos': 'Nigeria',
            'abuja': 'Nigeria',
            'addis ababa': 'Ethiopia',
            'accra': 'Ghana',
            'dar es salaam': 'Tanzania',
            'kampala': 'Uganda',
        }

        # Check each pattern
        for pattern, country in country_patterns.items():
            if pattern in location_lower:
                return country

        # If no match found, return None
        return None

    def generate_xml(self) -> None:
        """Generate XML configuration file."""
        print(f"\nGenerating XML: {self.output_file}")

        # Create root element
        root = ET.Element('Config')

        # Add comment
        comment = ET.Comment(f'''
BFPO Address Configuration
Generated from GOV.UK BFPO locations
Last Updated: {datetime.now().strftime("%Y-%m-%d")}
Created By: Affinis Ltd (Dominic Digby)
Schema: bfpo_config.xsd
Country Codes: ISO 3166-1 alpha-2 (via pycountry)
''')
        root.append(comment)

        # Sort addresses by BFPO number (extract numeric part)
        def get_sort_key(addr):
            bfpo_num = addr['BfpoNum'].replace('BFPO ', '').strip()
            return int(bfpo_num) if bfpo_num.isdigit() else 999

        self.addresses.sort(key=get_sort_key)

        # Add BFPO addresses
        for addr in self.addresses:
            addr_elem = ET.SubElement(root, 'BFFO_Address')

            # Required fields
            ET.SubElement(addr_elem, 'BfpoNum').text = addr['BfpoNum']

            # Optional BoxNum (for isolated detachments)
            if 'BoxNum' in addr:
                ET.SubElement(addr_elem, 'BoxNum').text = addr['BoxNum']

            ET.SubElement(addr_elem, 'Loc').text = addr['Loc']

            # Optional fields
            if 'PstCd' in addr:
                ET.SubElement(addr_elem, 'PstCd').text = addr['PstCd']
            if 'Ctry' in addr:
                ET.SubElement(addr_elem, 'Ctry').text = addr['Ctry']
            if 'CtryCd' in addr and addr['CtryCd']:
                ET.SubElement(addr_elem, 'CtryCd').text = addr['CtryCd']

            # Type (required)
            ET.SubElement(addr_elem, 'Type').text = addr['Type']

        # Write with pretty formatting
        self._write_pretty_xml(root, self.output_file)

        print(f"✓ Generated XML with {len(self.addresses)} BFPO addresses")

        # Print country code statistics
        self._print_country_stats()

    def _print_country_stats(self) -> None:
        """Print statistics about country code resolution."""
        total_with_country = sum(1 for addr in self.addresses if 'Ctry' in addr)
        total_with_code = sum(1 for addr in self.addresses if 'CtryCd' in addr)

        print("\nCountry Code Statistics:")
        print(f"  Addresses with country name: {total_with_country}")
        print(f"  Addresses with country code: {total_with_code}")

        if total_with_country > total_with_code:
            unmapped = total_with_country - total_with_code
            print(f"  ⚠ Unmapped countries: {unmapped}")

            # Show which countries failed to map
            unmapped_countries = set()
            for addr in self.addresses:
                if 'Ctry' in addr and 'CtryCd' not in addr:
                    unmapped_countries.add(addr['Ctry'])

            if unmapped_countries:
                print(f"  Unmapped country names: {', '.join(sorted(unmapped_countries))}")

    def _write_pretty_xml(self, root, filename: str) -> None:
        """Write XML with pretty formatting."""
        rough_string = ET.tostring(root, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="\t", encoding='utf-8')

        with open(filename, 'wb') as f:
            f.write(pretty_xml)

    def run(self) -> None:
        """Main execution method."""
        print("=" * 80)
        print("BFPO Data Scraper - Simplified Schema (with pycountry)")
        print("=" * 80)

        # Scrape GOV.UK
        self.scrape_gov_uk_bfpo()

        # Handle FCDO ODS file
        ods_file = None
        cleanup_temp = False

        if self.fcdo_ods_file:
            # Use pre-downloaded file
            print(f"\nUsing pre-downloaded FCDO ODS file: {self.fcdo_ods_file}")
            ods_file = self.fcdo_ods_file
        else:
            # Try to download
            ods_file = self.download_fcdo_ods()
            cleanup_temp = True

        # Parse FCDO data if we have a file
        if ods_file:
            if os.path.exists(ods_file):
                self.parse_fcdo_ods(ods_file)

                # Clean up temp file if we downloaded it
                if cleanup_temp:
                    try:
                        os.unlink(ods_file)
                        print(f"✓ Cleaned up temporary file: {ods_file}")
                    except:
                        pass
            else:
                print(f"✗ FCDO ODS file not found: {ods_file}")
        else:
            print("\n⚠ Skipping FCDO data (file not available)")
            print("  To include FCDO data, download the ODS file manually and provide path:")
            print(f"  {self.FCDO_ODS_URL}")

        # Generate XML
        self.generate_xml()

        print("\n" + "=" * 80)
        print(f"✓ Complete! Generated: {self.output_file}")
        print("=" * 80)


def main() -> None:
    """Main entry point."""

    # Check if FCDO ODS file was provided as argument
    fcdo_file = None
    if len(sys.argv) > 1:
        fcdo_file = sys.argv[1]
        print(f"Using FCDO ODS file: {fcdo_file}")

    scraper = BFPOScraperSimple(
        output_file="bfpo_config.xml",
        fcdo_ods_file=fcdo_file
    )
    scraper.run()


if __name__ == "__main__":
    main()
