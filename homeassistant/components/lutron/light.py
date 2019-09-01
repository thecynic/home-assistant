"""Support for Lutron lights."""
import logging

from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light

from . import LUTRON_CONTROLLER, LUTRON_DEVICES, LutronDevice

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Lutron lights."""
    devs = []
    for (area_name, device) in hass.data[LUTRON_DEVICES]["light"]:
        dev = LutronLight(area_name, device, hass.data[LUTRON_CONTROLLER])
        devs.append(dev)

    add_entities(devs, True)


def to_lutron_level(level):
    """Convert the given HASS light level (0-255) to Lutron (0.0-100.0)."""
    return float((level * 100) / 255)


def to_hass_level(level):
    """Convert the given Lutron (0.0-100.0) light level to HASS (0-255)."""
    return int((level * 255) / 100)


class LutronLight(LutronDevice, Light):
    """Representation of a Lutron Light, including dimmable."""

    def __init__(self, area_name, lutron_device, controller):
        """Initialize the light."""
        self._prev_brightness = None
        super().__init__(area_name, lutron_device, controller)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        new_brightness = to_hass_level(self._lutron_device.last_level())
        _LOGGER.debug('Getting brightness: %d (prev %d) @ %s' % (
                new_brightness, self._prev_brightness, self._lutron_device))
        if new_brightness != 0:
            self._prev_brightness = new_brightness
        return new_brightness

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs and self._lutron_device.is_dimmable:
            brightness = kwargs[ATTR_BRIGHTNESS]
            source = "attrs"
        elif self._prev_brightness == 0:
            brightness = 255 / 2
            source = "default"
        else:
            brightness = self._prev_brightness
            source = "previous"
        _LOGGER.debug('Turning on: brightness: %d (prev %d source %s) @ %s' % (
                brightness, self._prev_brightness, source, self._lutron_device))
        self._prev_brightness = brightness
        _LOGGER.debug("In on: set prev %d @ %s" % (
                self._prev_brightness, self._lutron_device))
        self._lutron_device.level = to_lutron_level(brightness)
        _LOGGER.debug('Turned on: brightness: %d (prev %d source %s) @ %s' % (
                to_hass_level(self._lutron_device.last_level()), self._prev_brightness, source, self._lutron_device))

    def turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.debug("Turning off (prev %d) @ %s" % (
                self._prev_brightness, self._lutron_device))
        self._lutron_device.level = 0
        _LOGGER.debug("Turned off (prev %d) @ %s" % (
                self._prev_brightness, self._lutron_device))

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = {"lutron_integration_id": self._lutron_device.id}
        return attr

    @property
    def is_on(self):
        """Return true if device is on."""
        last = self._lutron_device.last_level()
        _LOGGER.debug("Checking on state: on %s last %f prev %d @ %s" % (
                last > 0, last, self._prev_brightness, self._lutron_device))
        return self._lutron_device.last_level() > 0

    def update(self):
        """Call when forcing a refresh of the device."""
        if self._prev_brightness is None:
            self._prev_brightness = to_hass_level(self._lutron_device.level)
            _LOGGER.debug("In update: setting prev %d @ %s" % (
                    self._prev_brightness, self._lutron_device))
        else:
            _LOGGER.debug("In update: prev %d @ %s" % (
                    self._prev_brightness, self._lutron_device))
