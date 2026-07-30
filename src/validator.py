"""EPUB validation."""
from __future__ import annotations

import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class EPUBValidator:
    """Validates EPUB files for compatibility."""

    REQUIRED_FILES = [
        "mimetype",
        "META-INF/container.xml",
    ]

    # Files that may be inside EPUB/ subdirectory
    REQUIRED_CONTENT_FILES = [
        "content.opf",
        "toc.ncx",
    ]

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self, epub_path: Path) -> tuple[bool, list[str], list[str]]:
        """Validate an EPUB file."""
        self.errors = []
        self.warnings = []

        if not epub_path.exists():
            self.errors.append(f"File not found: {epub_path}")
            return False, self.errors, self.warnings

        try:
            with zipfile.ZipFile(epub_path, "r") as zf:
                file_list = zf.namelist()
                self._check_required_files(file_list)
                self._check_content_files(file_list)
                self._check_mimetype(zf)
                self._check_opf(zf, file_list)
                self._check_ncx(zf, file_list)
                self._check_xhtml_files(zf)

        except zipfile.BadZipFile:
            self.errors.append("Invalid ZIP/EPUB file")
        except Exception as e:
            self.errors.append(f"Validation error: {e}")

        return len(self.errors) == 0, self.errors, self.warnings

    def _find_file(self, file_list: list[str], filename: str) -> str | None:
        """Find a file in the archive, checking EPUB/ subdirectory."""
        if filename in file_list:
            return filename
        epub_path = f"EPUB/{filename}"
        if epub_path in file_list:
            return epub_path
        # Also check for any nested path
        for f in file_list:
            if f.endswith(f"/{filename}") or f.endswith(f"\\{filename}"):
                return f
        return None

    def _check_required_files(self, file_list: list[str]) -> None:
        """Check for required EPUB files."""
        for required in self.REQUIRED_FILES:
            if required not in file_list:
                self.errors.append(f"Missing required file: {required}")

    def _check_content_files(self, file_list: list[str]) -> None:
        """Check for content files (opf, ncx) that may be in EPUB/ subdirectory."""
        for filename in self.REQUIRED_CONTENT_FILES:
            if self._find_file(file_list, filename) is None:
                self.errors.append(f"Missing required file: {filename}")

    def _check_mimetype(self, zf: zipfile.ZipFile) -> None:
        """Check mimetype file content."""
        try:
            mimetype = zf.read("mimetype").decode("utf-8").strip()
            if mimetype != "application/epub+zip":
                self.errors.append(f"Invalid mimetype: {mimetype}")
        except KeyError:
            self.errors.append("mimetype file not found")

    def _check_opf(self, zf: zipfile.ZipFile, file_list: list[str]) -> None:
        """Check OPF file validity."""
        opf_path = self._find_file(file_list, "content.opf")
        if not opf_path:
            self.errors.append("content.opf file not found")
            return

        try:
            opf_content = zf.read(opf_path).decode("utf-8")
            if not opf_content:
                self.errors.append("Empty content.opf file")
                return

            # Check for required elements
            required_elements = ["<metadata", "<manifest", "<spine"]
            for elem in required_elements:
                if elem not in opf_content:
                    self.errors.append(f"Missing element in content.opf: {elem}")

        except KeyError:
            self.errors.append(f"Cannot read content.opf from {opf_path}")

    def _check_ncx(self, zf: zipfile.ZipFile, file_list: list[str]) -> None:
        """Check NCX file validity."""
        ncx_path = self._find_file(file_list, "toc.ncx")
        if not ncx_path:
            self.errors.append("toc.ncx file not found")
            return

        try:
            ncx_content = zf.read(ncx_path).decode("utf-8")
            if not ncx_content:
                self.errors.append("Empty toc.ncx file")
                return

            # Check for required elements
            if "<ncx" not in ncx_content:
                self.errors.append("Invalid NCX file format")

        except KeyError:
            self.errors.append(f"Cannot read toc.ncx from {ncx_path}")

    def _check_xhtml_files(self, zf: zipfile.ZipFile) -> None:
        """Check XHTML files for basic validity."""
        xhtml_files = [f for f in zf.namelist() if f.endswith((".xhtml", ".html"))]

        if not xhtml_files:
            self.warnings.append("No XHTML content files found")

        for xhtml_file in xhtml_files[:5]:  # Check first 5 files
            try:
                content = zf.read(xhtml_file).decode("utf-8")
                if not content.strip():
                    self.warnings.append(f"Empty XHTML file: {xhtml_file}")
                elif "<html" not in content.lower():
                    self.warnings.append(f"Missing HTML tag in: {xhtml_file}")
            except Exception as e:
                self.warnings.append(f"Error reading {xhtml_file}: {e}")

    def get_report(self) -> str:
        """Get a validation report."""
        report = []
        if self.errors:
            report.append("Errors:")
            for error in self.errors:
                report.append(f"  - {error}")
        if self.warnings:
            report.append("Warnings:")
            for warning in self.warnings:
                report.append(f"  - {warning}")
        if not self.errors and not self.warnings:
            report.append("EPUB is valid!")

        return "\n".join(report)
