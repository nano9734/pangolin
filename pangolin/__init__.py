# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
"""Pangolin Package Initialization

This package provides the core components for running Pangolin:

Modules:
    config (Config)        : Handles configuration loading and validation.
    factory (UrlFactory)   : Generates a WebSocket URL for a supported exchange.
    manager (StreamManager): Manages real-time data streams and coordinates strategy modules.
"""

from .config import Config
from .factory import UrlFactory
from .database import Database
from .manager import StreamManager
