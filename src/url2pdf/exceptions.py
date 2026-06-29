"""url2pdf - custom exceptions."""


class Url2PdfError(Exception):
    """Base exception for all url2pdf errors."""


class PageLoadError(Url2PdfError):
    """Raised when the target page cannot be loaded."""


class PDFGenerationError(Url2PdfError):
    """Raised when Playwright fails to produce a PDF."""
