#!/usr/bin/python3.5

################################################################################
# library.py - Library of functions for stats_model_logger.py   
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
################################################################################

# import required modules
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

# globals
config_path = "stats_model_logger.conf"
update_interval = False
data_model = False
status_flag = False

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

# try checking the config file exists and it can be opened, else throw
# I/O error then display failure message and exit agent.
def check_config_file():
  global config_path
  try:
    if os.path.exists(config_path):
      try:
        fd = open(config_path, "r")
        fd.close()
      except IOError:
        print("FAILURE: Failed to read configuration file " % config_path)
        sys.exit()
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to open configuration file " % config_path)
    sys.exit()

# check options in config file
def check_config_options():
  global config_path
  global update_interval
  global data_model
  # try opening config file for reading options, else throw I/O error then
  # display failure message and exit agent.  
  try:
    if os.path.exists(config_path):
      configfile = open(config_path, "r")
      configfile.seek(0)
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to open configuration file " % config_path)
    configfile.close()
    sys.exit()
  for line in configfile:
    # try checking format of update-interval in config file, else throw value
    # error then display failure message and exit agent.    
    if re.match("^update\-interval\:", line):
      if update_interval is False:
        try:
          # get value of option
          _, optval = line.split(':', 2)
          optval = optval.strip()
          # check update-interval pattern
          if re.match("[1-9]{1,8}", optval):
            # keep update-interval for agent
            update_interval = int(optval)
          else:
            raise ValueError
        except ValueError:
          print("FAILURE: Invalid format of update-interval " % update_interval)
          configfile.close()
          sys.exit()
      else:
        pass
    # try converting data-model in config file to dictionary, else throw value
    # error then display failure message and exit agent. 
    elif re.match("^data\-model\:", line):
      if data_model is False: 
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
              data_model = True
          if data_model is True:
            # keep data-model for agent 
            data_model = tmpdict
            del tmpdict
          elif data_model is False:
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
    if os.path.exists(config_path):
      configfile.close()
    else:
      raise IOError
  except IOError:
    print("FAILURE: Failed to close configuration file " % config_path)
    sys.exit()
 
# run required checks
check_distribution()
check_dependencies()
check_config_file()
check_config_options()

# remove code for checks 
del check_distribution
del check_dependencies
del check_config_file
del check_config_options   

# try checking service status of rsyslog, else throw OSError. if rsyslog is
# running, set flag to true. if rsyslog is not running, set flag to false.
def check_rsyslog_status():
  global status_flag
  try:
    status, _ = syscmd("service rsyslog status")
    if "Active: active (running)" in status:
      status_flag = True
    else:
      raise OSError
  except OSError:
    print("WARNING: Rsyslog not running. Redirecting JSON to logs/stats_model_logger/timestamp")
    status_flag = False

# check status of rsyslog service before logging data. if rsyslog is running,
# use logger. if rsyslog is not running, append data to new file at
# "logs/stats_model_logger/timestamp".
def log_data():
  global update_interval
  global data_model
  global status_flag
  check_rsyslog_status()
  # use logger to send data to local rsyslog service
  if status_flag is True:    
    _, _ = syscmd("logger -t STATS_MODEL_LOGGER.PY %s" % data_model)
  # append data to new file
  else:
    timestamp = calendar.timegm(time.gmtime())
    if os.path.exists("logs/stats_model_logger"):
      _, _ = syscmd("echo %s >> logs/stats_model_logger/%s" % (data_model, timestamp))
    else:
      _, _ = syscmd("mkdir -p logs/stats_model_logger")
      _, _ = syscmd("echo %s >> logs/stats_model_logger/%s" % (data_model, timestamp))

# get value and timestamp, append to key in dictionary. 
def get_values():
  global data_model
  # create temporary dictionary
  tmpdict = collections.OrderedDict()
  # get values for keys in dictionary using syscmd()
  for key,command in data_model.items():
    value, timestamp = syscmd(command[0])
    # add value and timestamp of key to temporary dictionary
    keyname = "'%s'" % key
    tmpdict.update({keyname: [value, timestamp]})
  # replace data_model with tmpdict
  data_model = tmpdict
  del tmpdict
  # convert dictionary to json
  data_model = json.dumps(data_model, ensure_ascii=False)

