"""Errors for the Axis component."""
from homeassistant.exceptions import HomeAssistantError


class AnycubicException(HomeAssistantError):
    """Base class for Anycubic exceptions."""


class AnycubicMonoXAPILevel(AnycubicException):
    """Problem with API."""
