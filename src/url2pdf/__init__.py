"""url2pdf - convert any web page to a searchable PDF."""

from .converter import convert, convert_url_async, make_filename
from .exceptions import PageLoadError, PDFGenerationError, Url2PdfError

__all__ = [
    "convert",
    "convert_url_async",
    "make_filename",
    "Url2PdfError",
    "PageLoadError",
    "PDFGenerationError",
]

__version__ = "1.2.0"
