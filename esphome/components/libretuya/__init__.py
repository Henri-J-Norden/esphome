import logging

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_BOARD,
    CONF_FRAMEWORK,
    CONF_SOURCE,
    CONF_VERSION,
    KEY_CORE,
    KEY_FRAMEWORK_VERSION,
    KEY_TARGET_FRAMEWORK,
    KEY_TARGET_PLATFORM,
)
from esphome.core import CORE

from .const import KEY_BOARD, KEY_LIBRETUYA, libretuya_ns

_LOGGER = logging.getLogger(__name__)
CODEOWNERS = ["@kuba2k2"]
AUTO_LOAD = []


def _set_core_data(config):
    CORE.data[KEY_LIBRETUYA] = {}
    CORE.data[KEY_CORE][KEY_TARGET_PLATFORM] = "libretuya"
    CORE.data[KEY_CORE][KEY_TARGET_FRAMEWORK] = "arduino"
    CORE.data[KEY_CORE][KEY_FRAMEWORK_VERSION] = cv.Version.parse(
        config[CONF_FRAMEWORK][CONF_VERSION]
    )
    CORE.data[KEY_LIBRETUYA][KEY_BOARD] = config[CONF_BOARD]
    return config


# NOTE: Keep this in mind when updating the recommended version:
#  * For all constants below, update platformio.ini (in this repo)
ARDUINO_VERSIONS = {
    "dev": (cv.Version(0, 4, 0), "https://github.com/kuba2k2/libretuya.git"),
    "latest": (cv.Version(0, 4, 0), None),
    "recommended": (cv.Version(0, 4, 0), None),
}


def _check_framework_version(value):
    value = value.copy()

    if value[CONF_VERSION] in ARDUINO_VERSIONS:
        if CONF_SOURCE in value:
            raise cv.Invalid(
                "Framework version needs to be explicitly specified when custom source is used."
            )

        version, source = ARDUINO_VERSIONS[value[CONF_VERSION]]
    else:
        version = cv.Version.parse(cv.version_number(value[CONF_VERSION]))
        source = value.get(CONF_SOURCE, None)

    value[CONF_VERSION] = str(version)
    value[CONF_SOURCE] = source or f"~{version.major}.{version.minor}.{version.patch}"

    return value


FRAMEWORK_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Optional(CONF_VERSION, default="recommended"): cv.string_strict,
            cv.Optional(CONF_SOURCE): cv.string_strict,
        }
    ),
    _check_framework_version,
)

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Required(CONF_BOARD): cv.string_strict,
            cv.Optional(CONF_FRAMEWORK, default={}): FRAMEWORK_SCHEMA,
        },
    ),
    _set_core_data,
)


async def to_code(config):
    cg.add(libretuya_ns.setup_preferences())

    # setup board config
    cg.add_platformio_option("board", config[CONF_BOARD])
    cg.add_build_flag(f"-DUSE_LIBRETUYA")
    cg.add_define("ESPHOME_BOARD", config[CONF_BOARD])
    cg.add_define("ESPHOME_VARIANT", "LibreTuya")

    # setup LT logger to work nicely with ESPHome logger
    cg.add_build_flag("-DLT_LOGGER_CALLER=0")
    cg.add_build_flag("-DLT_LOGGER_TASK=0")
    cg.add_build_flag("-DLT_LOGGER_COLOR=1")

    # force using arduino framework
    cg.add_platformio_option("framework", "arduino")
    cg.add_build_flag("-DUSE_ARDUINO")

    # disable library compatibility checks
    cg.add_platformio_option("lib_ldf_mode", "off")
    # include <Arduino.h> in every file
    cg.add_platformio_option("build_src_flags", "-include Arduino.h")

    # if platform version is a valid version constraint, prefix the default package
    conf = config[CONF_FRAMEWORK]
    cv.platformio_version_constraint(conf[CONF_VERSION])
    cg.add_platformio_option("platform", f"libretuya @ {conf[CONF_VERSION]}")

    # dummy version code
    cg.add_define(
        "USE_ARDUINO_VERSION_CODE", cg.RawExpression(f"VERSION_CODE(0, 0, 0)")
    )