"""url2pdf - convert any web page to a searchable PDF."""

from .converter import convert, make_filename
from .exceptions import PageLoadError, PDFGenerationError, Url2PdfError

__all__ = [
    "convert",
    "make_filename",
    "Url2PdfError",
    "PageLoadError",
    "PDFGenerationError",
]

__version__ = "1.0.0"
