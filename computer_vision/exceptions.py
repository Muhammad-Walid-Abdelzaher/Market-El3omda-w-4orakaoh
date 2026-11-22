class ComputerVisionError(RuntimeError):
    """Base exception for the computer vision package."""


class ImageDecodeError(ComputerVisionError, ValueError):
    """Raised when image bytes cannot be decoded or validated."""


class ModelNotFoundError(ComputerVisionError, FileNotFoundError):
    """Raised when a required model weight file is missing."""


class ModelInferenceError(ComputerVisionError):
    """Raised when model inference fails."""

