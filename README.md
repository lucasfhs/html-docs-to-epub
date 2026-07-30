# Documentation to EPUB Converter

Transforme sites de documentacao online em arquivos EPUB compativeis com Kindle.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Command Line Arguments](#command-line-arguments)
- [How It Works](#how-it-works)
- [Cache System](#cache-system)
- [Kindle Compatibility](#kindle-compatibility)
- [Send to Kindle](#send-to-kindle)
- [Supported Sites](#supported-sites)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| Automatic Discovery | Finds pages via sitemaps, navigation menus, and link crawling |
| Content Extraction | Removes navigation, ads, menus, and irrelevant elements |
| Image Processing | Downloads, optimizes, and compresses images |
| Chapter Organization | Follows documentation structure with proper hierarchy |
| Navigable TOC | Works with Kindle, Calibre, Apple Books, Kobo, and more |
| Internal Links | Converts documentation links to EPUB internal references |
| Code Preservation | Maintains code blocks with proper formatting |
| Cache System | Resume interrupted conversions without starting over |
| Progress Bars | Visual feedback for all long operations |
| Respectful Crawling | Rate limiting and robots.txt support |
| Send to Kindle | Send EPUB directly to your Kindle via email (SMTP) |

---

## Demo

### Starting the converter

```
$ python main.py

 Documentation to EPUB Converter
 Transform online documentation into Kindle-compatible EPUB files

Enter the documentation URL:
> https://hermes.aios.com.br/docs
```

### Discovering pages

```
Phase 1: Discovering pages...
Discovering pages: 100%|████████████████| 48/48
```

### Processing content

```
Phase 2: Processing content...
Processing images: 100%|████████████████| 122/122
```

### Building EPUB

```
Phase 3: Building EPUB...
Generating EPUB: 100%|████████████████| 1/1
```

### Validation

```
Phase 4: Validating EPUB...
✓ EPUB is valid!
```

### Sending to Kindle

```
Phase 5: Sending to Kindle...
Using SMTP server: smtp.gmail.com:587
Connecting to smtp.gmail.com:587...
✓ EPUB sent to user@kindle.com

┌─────────────────────── Summary ────────────────────────┐
│ Pages found:        48                                 │
│ Pages processed:    48                                 │
│ Pages skipped:      0                                  │
│ Images processed:   122                                │
│ Images skipped:     3                                  │
│ EPUB size:          18.4 MB                            │
│ Output file:        output/hermes-documentation.epub   │
│ Sent to Kindle:     Sent                               │
└────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Clone the repository

```bash
git clone https://github.com/yourusername/documentation-to-epub.git
cd documentation-to-epub
```

### Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Optional: Install Playwright

For JavaScript-rendered pages:

```bash
pip install playwright
playwright install chromium
```

---

## Usage

### Interactive Mode

```bash
python main.py
```

The program will guide you through the process step by step, including an option to send the EPUB to your Kindle via email.

### Command Line Mode

```bash
python main.py https://site.com/docs
```

### Full Example

```bash
python main.py https://hermes.aios.com.br/docs \
  --output hermes-docs.epub \
  --title "Hermes Agent Documentation" \
  --author "Hermes Team" \
  --max-pages 500 \
  --workers 5 \
  --image-quality 80 \
  --max-image-width 1200 \
  --delay 0.3
```

### Send to Kindle Example

```bash
python main.py https://site.com/docs \
  --send-to-kindle \
  --kindle-email user@kindle.com \
  --smtp-email user@gmail.com \
  --smtp-password your-app-password
```

---

## Command Line Arguments

### General Options

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `url` | - | Documentation URL | (interactive) |
| `--output` | `-o` | Output EPUB file path | `output/<title>.epub` |
| `--title` | `-t` | Book title | (auto-generated) |
| `--author` | `-a` | Book author | "Documentation Converter" |
| `--max-pages` | - | Maximum pages to process | 500 |
| `--workers` | - | Number of concurrent workers | 5 |
| `--delay` | - | Delay between requests (seconds) | 0.3 |
| `--image-quality` | - | JPEG image quality (1-100) | 80 |
| `--max-image-width` | - | Maximum image width in pixels | 1200 |
| `--use-playwright` | - | Use Playwright for JS pages | false |
| `--force` | - | Ignore cache, start fresh | false |
| `--no-images` | - | Exclude images from EPUB | false |
| `--include` | - | Regex pattern for URLs to include | (none) |
| `--exclude` | - | Regex pattern for URLs to exclude | (none) |
| `--verbose` | `-v` | Enable verbose output | false |

### Send to Kindle Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--send-to-kindle` | Send EPUB to Kindle via email after generation | false |
| `--kindle-email` | Kindle email address (e.g. `user@kindle.com`) | (none) |
| `--smtp-email` | Sender email address for SMTP | (none) |
| `--smtp-password` | Sender email password or app password | (none) |
| `--smtp-server` | SMTP server address (auto-detected from email) | (none) |
| `--smtp-port` | SMTP server port | 587 |
| `--smtp-no-tls` | Disable TLS encryption for SMTP connection | false |

---

## How It Works

### 1. URL Validation

The tool validates and normalizes the input URL, ensuring it has a proper scheme and format.

### 2. Sitemap Discovery

Checks for XML sitemaps at common locations (`/sitemap.xml`, `/sitemap_index.xml`, etc.) to discover documentation pages.

### 3. Page Crawling

Discovers documentation pages by following internal links, respecting:
- Same domain restriction
- Documentation section boundaries
- Rate limiting
- robots.txt rules

### 4. Content Extraction

Extracts the main content from each page using multiple strategies:
- CSS selectors (`.content`, `.documentation`, `main`, `article`, etc.)
- Heuristic analysis based on text density
- Readability algorithms

### 5. HTML Cleaning

Removes irrelevant elements while preserving content:
- Navigation menus
- Headers and footers
- Advertisements
- Social sharing buttons
- Scripts and styles
- Hidden elements

### 6. Image Processing

Handles images with optimization:
- Downloads and caches images
- Converts WebP to JPEG/PNG
- Resizes large images (max 1200px width)
- Compresses with configurable quality
- Removes tiny icons and tracking pixels

### 7. Link Conversion

Converts internal documentation links to EPUB references:
- Resolves relative URLs
- Maps pages to filenames
- Preserves external links
- Handles in-page anchors

### 8. Chapter Building

Organizes pages into chapters following:
- Menu/navigation order
- Sitemap order
- URL hierarchy
- Discovery order

### 9. EPUB Generation

Creates a valid EPUB 3 file with:
- Cover page
- Title page
- Table of contents (NCX + Navigation Document)
- Chapters with proper XHTML
- Embedded CSS styles
- Local images

### 10. Validation

Verifies the EPUB structure:
- Required files present
- Valid mimetype
- Proper OPF structure
- Working navigation
- Valid XHTML content

### 11. Send to Kindle (Optional)

If enabled, sends the generated EPUB to your Kindle via email:
- Auto-detects SMTP server from email address
- Supports TLS encryption (configurable)
- Works with Gmail, Outlook, Yahoo, Zoho, and more

---

## Cache System

The tool caches downloaded pages and images to allow resuming interrupted conversions.

### Cache Location

```
.cache/
  <project-name>/
    pages/          # Cached HTML pages
    images/         # Cached images
    metadata.json   # Session information
```

### Resume Interrupted Conversion

If a conversion is interrupted, run the tool again:

```
An incomplete processing session was found.
1. Continue processing
2. Restart processing
3. Cancel
> 1
```

### Clear Cache

Use the `--force` flag to ignore the cache:

```bash
python main.py https://site.com/docs --force
```

---

## Kindle Compatibility

The generated EPUB files follow conservative guidelines for maximum compatibility.

### Compatibility Matrix

| Device/Software | Status |
|-----------------|--------|
| Kindle (all models) | Fully compatible |
| Calibre | Fully compatible |
| Apple Books | Fully compatible |
| Kobo Reader | Fully compatible |
| Readium | Fully compatible |
| Thorium Reader | Fully compatible |

### Technical Details

- EPUB 3 format with fallback support
- Valid XHTML content
- No JavaScript dependencies
- No external font dependencies
- Conservative CSS styling
- Locally embedded images
- Proper navigation structure (NCX + Navigation Document)
- UTF-8 encoding for special characters

---

## Send to Kindle

The tool can send the generated EPUB directly to your Kindle via email using SMTP.

### Quick Start

**Interactive mode:**

```bash
python main.py
# Answer "y" when asked about sending to Kindle
```

**CLI mode:**

```bash
python main.py https://site.com/docs \
  --send-to-kindle \
  --kindle-email user@kindle.com \
  --smtp-email user@gmail.com \
  --smtp-password your-app-password
```

### Gmail Setup

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate a new app password for "Mail"
5. Use that password with `--smtp-password`

### Zoho Setup

```bash
python main.py https://site.com/docs \
  --send-to-kindle \
  --kindle-email user@kindle.com \
  --smtp-email user@zoho.com \
  --smtp-password your-zoho-password \
  --smtp-server smtp.zoho.com \
  --smtp-port 587
```

### Using .env File (Recommended)

Create a `.env` file in the project root to avoid typing credentials every time:

```
KINDLE_EMAIL=your-kindle@kindle.com
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

The `.env` file is already in `.gitignore` and will not be committed.

See `.env.example` for a template.

### Supported Providers

| Provider | SMTP Server | Port | TLS |
|----------|-------------|------|-----|
| Gmail | smtp.gmail.com | 587 | Yes |
| Outlook/Hotmail | smtp.office365.com | 587 | Yes |
| Yahoo | smtp.mail.yahoo.com | 587 | Yes |
| iCloud | smtp.mail.me.com | 587 | Yes |
| Zoho | smtp.zoho.com | 587 | Yes |

For other providers, the tool auto-detects the SMTP server from the email domain.

---

## Supported Sites

### Best Results

- Documentation sites with clear structure
- Technical documentation (libraries, frameworks, APIs)
- Static documentation (MkDocs, Docusaurus, Sphinx, GitBook)
- GitHub Pages documentation
- Read the Docs sites

### Limited Support

- Single-page applications with heavy JavaScript
- Sites requiring authentication
- Sites with aggressive anti-bot measures

### Tips for Better Results

1. Use a specific documentation URL (e.g., `/docs/getting-started/`)
2. For JS-heavy sites, try `--use-playwright`
3. Use `--include` to target specific sections
4. Check `--verbose` output for debugging

---

## Troubleshooting

### No pages found

- Verify the URL is correct
- Try a more specific URL
- Use `--verbose` to see detailed logs
- Check if the site requires authentication

### Images not loading

- Some images may be blocked by CORS
- Try with `--no-images` flag
- Check the log file in `logs/conversion.log`

### EPUB won't open

- Ensure the file wasn't corrupted during download
- Try opening with Calibre to diagnose issues
- Check the validation output

### Slow conversion

- Reduce `--workers` for slow sites
- Increase `--delay` to be more respectful
- Use `--max-pages` to limit scope

### Missing content

- The site may use JavaScript to load content
- Try `--use-playwright` for dynamic sites
- Use `--include` to target specific sections

### Send to Kindle fails

- Check your email and password are correct
- For Gmail, use an App Password (not your regular password)
- Verify the SMTP server and port are correct
- Try `--verbose` to see detailed SMTP logs
- Some providers block automated emails - check your spam folder

---

## Project Structure

```
documentation-to-epub/
├── main.py                 # Entry point
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
├── README.md               # Documentation
├── .gitignore              # Git ignore rules
├── .env.example            # Environment variables template
├── assets/
│   └── book.css            # EPUB stylesheet
├── src/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration
│   ├── models.py           # Data models
│   ├── crawler.py          # Web crawler
│   ├── sitemap.py          # Sitemap parser
│   ├── extractor.py        # Content extraction
│   ├── cleaner.py          # HTML cleaning
│   ├── image_processor.py  # Image processing
│   ├── link_converter.py   # Link conversion
│   ├── chapter_builder.py  # Chapter building
│   ├── epub_builder.py     # EPUB generation
│   ├── validator.py        # EPUB validation
│   ├── sender.py           # Send to Kindle via email
│   ├── cache.py            # Cache system
│   ├── progress.py         # Progress display
│   └── utils.py            # Utilities
├── tests/                  # Automated tests
├── output/                 # Generated EPUBs
└── logs/                   # Conversion logs
```

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/documentation-to-epub.git
cd documentation-to-epub

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
pytest tests/ -v
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
