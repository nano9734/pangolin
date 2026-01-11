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

class UrlFactory:
    def __init__(self):
        self.CREATE_SUCCESS_MSG = '[UrlFactory] WebSocket URL has been successfully assembled:'

    def create_wss_url(self, enabled_exchange_name:str, netloc: str, ticker: str) -> str:
        if enabled_exchange_name == 'binance':
            wss_url = 'wss://' + netloc + '/ws/' + ticker + '@aggTrade'
            print(self.CREATE_SUCCESS_MSG, wss_url)
            print() # Add a line break for console readability
            return wss_url
