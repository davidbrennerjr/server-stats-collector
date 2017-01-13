#!/usr/bin/python3.5

################################################################################
# stats-model-logger.py - Periodically saves stats via model to rsyslog
#
# Copyright 2016 by David Brenner Jr <david.brenner.jr@gmail.com>
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
# ./stats-model-logger.py 
#
# Configuration Files
# stats-model-logger.conf
#
# Configuration Options
# update-interval: <number of seconds between updates>
# data-model:  
# <key name> = <system command that returns value>
# <key name> = <system command that returns value>
# <key name> = <system command that returns value>
################################################################################

try:
  import sys
  import platform
  import subprocess
  import os
  import re
  import time
  import calendar
  import json
  import collections
  import threading
except ImportError:
  print("FAILURE: Failed to import required modules")
  sys.exit()

CONFIG_PATH = "stats-model-logger.conf"
UPDATE_INTERVAL = False
DATA_MODEL = False

# exec system command, return output with timestamp
def syscmd(command): 
  if command != 0 or command != "":  
    command2 = "%s" % command
    try:
      p = subprocess.Popen(command2, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)    
      # ignore errors
      output, _ = p.communicate()
      timestamp = calendar.timegm(time.gmtime())
    except ValueError or OSError:
      p.kill()
  else:
    pass
  return output, timestamp

# try checking operating system name and operating system version exists
# in list of supported operating systems, else throw OS error then
# display non-critical warning message.   
def check_distribution():
  try:
    tested_os = {"Ubuntu":16, "Test1":1, "Test2":2}
    os_name, os_version, _ = platform.linux_distribution()
    if str(os_name) in tested_os.keys():
      if int(round(float(os_version),0)) != tested_os[os_name]:     
        print("WARNING: Distribution not supported: %s %s" % (os_name, os_version))
        raise OSError
      else:
        pass
    else:
      print("WARNING: Distribution not supported: %s %s" % (os_name, os_version)) 
      raise OSError
  except OSError:
    os_list = ""
    for key in tested_os:
      os_list = os_list + key + " " + str(tested_os[key]) + ", "
    print("Supported distributions: %s" % os_list[:-2])
# run required check
check_distribution()
# remove unused code
del check_distribution
del platform

# try querying the package management system for the status of the required
# package named "curl", else throw OS error then display failure message
# and exit agent.
def check_dependencies():
  try:
    package, _ = syscmd("dpkg-query -W --showformat='${Package} ${Status} ${Version}\n' util-linux")
    package = package.strip()
    if "util-linux install ok installed" not in package:
      raise OSError
    else:
      pass
  except OSError:
    print("FAILURE: logger not installed: %s" % package)
    sys.exit()
  try:
    package, _ = syscmd("dpkg-query -W --showformat='${Package} ${Status} ${Version}\n' rsyslog")
    package = package.strip()
    if "rsyslog install ok installed" not in package:
      raise OSError
    else:
      pass
  except OSError:
    print("FAILURE: rsyslog not installed: %s" % package)
    sys.exit()
# run required check 
check_dependencies()
# remove unused code
del check_dependencies

# try checking the config file exists and it can be opened, else throw
# I/O error then display failure message and exit agent.
def check_config_file():
  global CONFIG_PATH
  try:
    if os.path.exists(CONFIG_PATH):
      try:
        fd = open(CONFIG_PATH, "r")
        fd.close()
      except IOError:
        print("FAILURE: Failed to read configuration file " % CONFIG_PATH)
        sys.exit()
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to open configuration file " % CONFIG_PATH)
    sys.exit()
# run required check
check_config_file()
# remove unused code
del check_config_file

# check options in config file
def check_config_options():
  global CONFIG_PATH
  global UPDATE_INTERVAL
  global DATA_MODEL
  # try opening config file for reading options, else throw I/O error then
  # display failure message and exit agent.  
  try:
    if os.path.exists(CONFIG_PATH):
      configfile = open(CONFIG_PATH, "r")
      configfile.seek(0)
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to open configuration file " % CONFIG_PATH)
    configfile.close()
    sys.exit()
  for line in configfile:
    # try checking format of update-interval in config file, else throw value
    # error then display failure message and exit agent.    
    if re.match("^update\-interval\:", line):
      if UPDATE_INTERVAL is False:
        try:
          # get value of option
          _, optval = line.split(':', 2)
          optval = optval.strip()
          # check update-interval pattern
          if re.match("[1-9]{1,8}", optval):
            # keep update-interval for agent
            UPDATE_INTERVAL = int(optval)
          else:
            raise ValueError
        except ValueError:
          print("FAILURE: Invalid format of update-interval " % UPDATE_INTERVAL)
          configfile.close()
          sys.exit()
      else:
        pass
    # try converting data-model in config file to dictionary, else throw value
    # error then display failure message and exit agent. 
    elif re.match("^data\-model\:", line):
      if DATA_MODEL is False: 
        try:
          # create temporary ordered dictionary
          tmpdict = collections.OrderedDict()
          # get next line 
          next = configfile.readline()
          next = next.strip()
          # check all lines after "data-model:" for pairs
          for next in configfile:
            if re.match("^#{1}", next):
              pass
            elif re.match("^\s?\n{1}", next):
              pass
            elif next is None:
              pass
            else:
              # get the pair
              optkey, optcmd = next.split('=', 2)
              optkey = optkey.strip()
              optcmd = optcmd.strip()
              # add key and command to dictionary 
              tmpdict.update({str(optkey):[str(optcmd)]})
              DATA_MODEL = True
          if DATA_MODEL is True:
            # keep data-model for agent 
            DATA_MODEL = tmpdict
            del tmpdict
          elif DATA_MODEL is False:
            raise ValueError
          else:
            pass
        except ValueError:
          print("FAILURE: Invalid format of kvp in input model")
          configfile.close()
          sys.exit()
      else:
        pass        
    else:
      pass
  # try closing config file, else throw I/O error then display failure message
  # and exit agent.  
  try:
    if os.path.exists(CONFIG_PATH):
      configfile.close()
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to close configuration file " % CONFIG_PATH)
    sys.exit()
# run required check
check_config_options()
# remove unused code
del check_config_options
del os
del re

# get value and timestamp, append to key in dictionary. 
def get_values():
  global DATA_MODEL
  # create temporary dictionary
  tmpdict = collections.OrderedDict()
  # get values for keys in dictionary using syscmd()
  for key,command in DATA_MODEL.items():
    value, timestamp = syscmd(command[0])
    # add value and timestamp of key to temporary dictionary
    keyname = "'%s'" % key
    tmpdict.update({keyname: [value, timestamp]})
  # replace DATA_MODEL with tmpdict
  DATA_MODEL = tmpdict
  del tmpdict
  # convert dictionary to json
  DATA_MODEL = json.dumps(DATA_MODEL, ensure_ascii=False) 
   
# if update-interval is specified in config file, increment timer using value
if UPDATE_INTERVAL is not False:
  while True:
    threading.Timer(int(UPDATE_INTERVAL), get_values, ()).start() 
    time.sleep(UPDATE_INTERVAL)
    # use logger to send data to local rsyslog service
    _, _ = syscmd("logger -t stats-model-logger %s" % DATA_MODEL)   
# else assume admin will be using cron/at to periodically run this script 
else:
  get_values()
  # use logger to send data to local rsyslog service
  _, _ = syscmd("logger -t stats-model-logger %s" % DATA_MODEL)

sys.exit()

