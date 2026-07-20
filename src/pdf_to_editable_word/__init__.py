"""Layout-preserving PDF to editable DOCX conversion."""

from .converter import convert_pdf, inspect_pdf, validate_docx

__all__ = ["convert_pdf", "inspect_pdf", "validate_docx"]
__version__ = "0.1.0"
