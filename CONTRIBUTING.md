# Contributing to BFPO Address Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to the BFPO Address Scraper project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/domdigby/bfpo-scraper.git
   cd bfpo-scraper
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Making Changes

### Create a Branch

```bash
git checkout -b feature/add-new-country-mapping
git checkout -b fix/fcdo-parsing-bug
git checkout -b docs/improve-readme
```

Branch naming:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions

### Types of Contributions

**Bug Fixes**
- Parsing errors
- Country code mapping issues
- XML generation problems

**New Features**
- Additional data sources
- New output formats

**Documentation**
- Improve README
- Add code comments
- Create usage examples

**Tests**
- Add test coverage
- Fix failing tests
- Add edge cases

## Testing

### Run Tests

```bash
python tests/test_country_codes.py
python tests/test_isolated_detachments.py
python tests/test_bfpo_prefix.py
```

### Writing Tests

```python
def test_new_feature():
    """Test description."""
    # Arrange
    scraper = BFPOScraperSimple()
    
    # Act
    result = scraper.some_method()
    
    # Assert
    assert result == expected
```

## Coding Standards

### Python Style

Follow PEP 8:

```python
# Good
def get_country_code(country_name: str) -> Optional[str]:
    """Get ISO country code."""
    return CountryCodeResolver.get_country_code(country_name)

# Type annotations required
# Docstrings for public methods
# Descriptive variable names
```

### Required
- ✅ Type annotations
- ✅ Docstrings for public methods
- ✅ No unused imports
- ✅ Handle errors gracefully
- ✅ Pylance compliance

## Submitting Changes

### Before Submitting

1. **Run all tests**
2. **Check code style**
3. **Update documentation**

### Commit Messages

```
Add support for Royal Fleet Auxiliary vessels

- Parse RFA table from GOV.UK
- Add Type='rfa' to schema
- Include tests

Fixes #123
```

### Create Pull Request

1. Push to your fork
2. Open PR on GitHub
3. Fill out PR template
4. Wait for review

## Areas for Contribution

### High Priority
- Additional country name mappings
- Support for more BFPO data sources
- Performance optimizations

### Medium Priority
- Additional output formats (CSV, JSON)
- Caching mechanisms
- Enhanced error handling

### Low Priority
- GUI interface
- Docker support

## Questions?

- Check [README.md](README.md)
- Search [Issues](https://github.com/domdigby/bfpo-scraper/issues)
- Email: info@affinis.co.uk

Thank you for contributing! 🎉