'''
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.

US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

Author:
    Jianbin Tang, jbtang@au1.ibm.com
Initial Version:
    Mar-2020
Function:
   Define some common functions
'''

import os
import pytz
from datetime import datetime

def get_sec(time_str):
    """Get Seconds from time."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def get_immediate_files(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isfile(os.path.join(a_dir, name))]

def get_unix_time(timestring,fmt =  "%m/%d/%Y-%H:%M:%S", timezone='US/Eastern'):
    # Create datetime object
    d = datetime.strptime(timestring, fmt)
    eastern = pytz.timezone(timezone)
    localized_time = eastern.localize(d)
    unix_timestamp = localized_time.timestamp()
    return unix_timestamp


def get_datetime(unix_timestamp, fmt =  "%m/%d/%Y-%H:%M:%S", timezone='US/Eastern'):
    my_datetime = datetime.fromtimestamp(unix_timestamp, tz=pytz.timezone(timezone))
    #my_datetime.strftime('%d.%m.%Y')
    date_fmt1 = my_datetime.strftime(fmt)
    return date_fmt1


if __name__ == '__main__':
    # timestring = my_datetime.strftime("%m/%d/%Y-%H:%M:%S")

    timestring = '12-20-2016 10:44:00'
    unix_t = get_unix_time(timestring,"%m-%d-%Y %H:%M:%S")
    print(unix_t)

    # timestring = '01/01/1900-00:00'
    # unix_t = get_unix_time(timestring, "%m/%d/%Y-%H:%M")
    # print(unix_t)
    #
    # timestring = '06/20/2016-20:18:29'
    # unix_t = get_unix_time(timestring)
    # print(unix_t)


    wrst_date =get_datetime(1506011205)
    print(wrst_date)
    
    '''
    wrst_date =get_datetime(1499810543.18)
    print(wrst_date)
    
    
    
    
    timestring = '07/11/2017-18:02:00'
    unix_t = get_unix_time(timestring)
    print(unix_t)
    '''

