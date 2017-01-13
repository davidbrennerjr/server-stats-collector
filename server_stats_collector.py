#!/usr/bin/python3.5

################################################################################
# server_stats_collector.py - Periodically collects stats of server via model,
# sends stats to local rsyslog service.
#
# Copyright 2016-2017 by David Brenner Jr <david.brenner.jr@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
# Usage
# ./server_stats_collector.py 
#
# Configuration Files
# server_stats_collector.conf
#
# Configuration Options
# update-interval: <number of seconds between updates>
# data-model:  
# <key name> = <system command that returns value>
# <key name> = <system command that returns value>
# <key name> = <system command that returns value>
################################################################################

if __name__ == "__main__":
  # import required modules
  try:
    import sys
    import time
    import threading
    import library
  except ImportError:
    print("FAILURE: Failed to import required modules")
    sys.exit()
  # import required globals
  try:
    from library import update_interval
  except NameError:
    print("FAILURE: Failed to import required globals from library module")
    sys.exit()
  # if update-interval is specified in config file increment timer using value,
  # else run once then exit.
  if update_interval is not False:
    while True:
      threading.Timer(int(update_interval), library.get_values, ()).start() 
      time.sleep(update_interval)
      library.log_data()  
  else:
    library.get_values()
    library.log_data()
  sys.exit()

