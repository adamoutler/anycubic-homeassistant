""""Significant change support"""
from typing import Any, Optional
from homeassistant.core import callback, HomeAssistant


@callback
def async_check_significant_change(
    hass: HomeAssistant, old_state: str, new_state: str, _: Any, **kwargs: Any
) -> Optional[bool]:
    """Significant Change Support. Insignificant changes are attributes only.
    :old_state: the previous state of the sensor.
    :new_state: the current state of the sensor
    :return: true if new state is different than old state."""
    if old_state != new_state:
        return True
    return False
