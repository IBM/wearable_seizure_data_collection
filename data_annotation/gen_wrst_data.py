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
    Generate each patient's data with pickle data format
'''

import os
import sys

print('Current working path is %s' % str(os.getcwd()))
sys.path.insert(0, os.getcwd())

import pandas as pd
import re
import numpy as np
import pickle
import platform
import zipfile
import shutil
from pathlib import Path
import argparse

from utils.common_func import get_immediate_subdirectories
from utils.common_func import get_datetime



parser = argparse.ArgumentParser(description='BCH Data annotation')

if platform.system() == 'Linux':
    parser.add_argument('-r','--root_dir', default='/bigdata/datasets/bch/REDCap_202109',
                        help='path to output prediction')
    parser.add_argument('-o', '--out_dir', default='/bigdata/datasets/bch/REDCap_202109_out',
                        help='path to output prediction')
elif platform.system() == 'Darwin':
    parser.add_argument('-r','--root_dir', default=os.path.join(Path.home(),'datasets/bch/REDCap_202109'),
                        help='path to output prediction')
    parser.add_argument('-o', '--out_dir', default=os.path.join(Path.home(),'datasets/bch/REDCap_202109_out'),
                        help='path to output prediction')
else:
    print('Unknown OS platform %s' % platform.system())
    exit()

parser.add_argument('--eda_shift', default=120, type=int,
                        help='post window size')


args = parser.parse_args()
root_dir = args.root_dir
out_dir  = args.out_dir
eda_shift = args.eda_shift # EDA is usually delayed

wrst_raw_data_dir = os.path.join(out_dir,'raw_data')
# sensors = ['ACC', 'BVP', 'EDA', 'HR', 'IBI', 'TEMP']
# skip HR, IBI to save space
sensors = ['ACC', 'BVP', 'EDA', 'TEMP']

os.makedirs(wrst_raw_data_dir, 0o777, True)
cut_at_start_sec = 30 # remove some data since data at the beginning are not accurate

# data columns
# Patient ID: get from the Cxxx in the directory, may cross check with excel to see if there any difference.
# Wrst Plate Date: from subdirectory if any. If not, default value is 99:99
# Wrst Location: judge from folder name, but how to deal with some has both wrist and ankle???
# Wrst sensors start datetime from csv patient_szr_num_per_test_date_file
# wrst sensors duration = num_record/fs
# Wrst sensors end datetime from csv patient_szr_num_per_test_date_file, end = start + duration
# sensor metadata, especially sampling rate
# Wrst btn press time from 1st line in tags.csv, if not exist, 99:99


#define regex for different dir
patient_dir_pattern = '^C[0-9]{3}$'
#patient_dir_pattern = '^C[3-9]{1}[0-9]{2}$'
# patient_dir_pattern = '^C123'
patient_dir_re = re.compile(patient_dir_pattern)
date_pattern ='^[0-9]{2}.[0-9]{2}.[0-9]{4}$'
date_re = re.compile(date_pattern)
invalid_pattern='99:99'
invalid_re = re.compile(invalid_pattern)

zip_path = 'tmp'
shutil.rmtree(zip_path, ignore_errors=True)
os.makedirs(zip_path, 0o777, True)

for root, dirs, files in os.walk(root_dir):
    dirs.sort()
    # dirs = ['C290', 'C309', 'C333', 'C372', 'C380', 'C387']
    for dir in dirs:
        # find Cxxx: xxx is a digit number
        if patient_dir_re.match(dir):

            wrst_data_dicts = []
            wrst_data_index = 0

            date_dirs = get_immediate_subdirectories(os.path.join(root_dir, root, dir))

            # date_dir should be mm.dd.yyyy format
            date_dirs.sort()
            for date_dir in date_dirs:
                full_date_dir = os.path.join(root_dir, root, dir, date_dir)
                if date_re.match(date_dir):# date folder, go deeper
                    print('\nProcessing Patient %s\'s %s...' % (dir, date_dir))
                    wrst_data_dirs = get_immediate_subdirectories(full_date_dir)

                    # generate a list of values
                    wrst_data_dirs.sort()
                    for wrst_data_dir in wrst_data_dirs:
                        full_wrst_data_dir = os.path.join(full_date_dir, wrst_data_dir)
                        # check the format is correct
                        if wrst_data_dir[0:4]== 'left' or wrst_data_dir[0:5]== 'right':

                            # unzip file
                            zip_found = False
                            files = os.listdir(full_wrst_data_dir)
                            for filename in sorted(files):
                                if filename.endswith('.zip') and os.path.isfile(
                                        os.path.join(full_wrst_data_dir, filename)):
                                    zipfile.ZipFile(os.path.join(full_wrst_data_dir, filename)).extractall(zip_path)
                                    print('Processing %s...' % (os.path.join(full_wrst_data_dir, filename)))

                                    full_wrst_data_dir = zip_path
                                    zip_found = True

                                    break  # only extract first zip file

                            wrst_data = {}

                            # print(full_wrst_data_dir)
                            full_tag_file_dir = os.path.join(full_wrst_data_dir, 'tags.csv')
                            try:
                                tags_data = pd.read_csv(full_tag_file_dir, header=None)
                                #tags_start_unix_t = int(tags_data.iloc[0])
                                wrst_data['tag_unix_t'] = tags_data.values
                            except:
                                tags_start_unix_t = -1
                                wrst_data['tag_unix_t'] = np.empty([0, 0])
                                #print('Warning! %s is empty or not exist!' % full_tag_file_dir)

                            sensor_start_unix_t = 0
                            dur_min = 9999999999999999999
                            for sensor in sensors:
                                # check if patient_szr_num_per_test_date_file exists
                                sensor_file_path = os.path.join(full_wrst_data_dir, sensor + '.csv')
                                if not os.path.exists(sensor_file_path):
                                    print(str('Error! %s does not exist!' % (sensor_file_path)))
                                    wrst_data[sensor + '_fs'] = -1
                                    wrst_data[sensor] = np.empty([0, 0])
                                    continue

                                try:
                                    sensor_data = pd.read_csv(sensor_file_path, header=None)
                                except:
                                    print(str('Error! %s has no data!' % (sensor_file_path)))
                                    wrst_data[sensor + '_fs'] = -1
                                    wrst_data[sensor] = np.empty([0, 0])
                                    continue

                                # make sure all sensor has same start unix t
                                if sensor_start_unix_t == 0:
                                    if sensor!='HR':
                                        sensor_start_unix_t = int(np.round(sensor_data.iloc[0][0])) + cut_at_start_sec
                                    else:
                                        sensor_start_unix_t = int(np.round(sensor_data.iloc[0][0])) + cut_at_start_sec - 10
                                else:
                                    new_t = int(np.round(sensor_data.iloc[0][0]))
                                    if sensor!='HR' and sensor_start_unix_t != new_t+cut_at_start_sec:
                                        print('Error! %s\'s start time: %d not equal to others: %d, maybe start part been cut' % (sensor_file_path, new_t, sensor_start_unix_t))
                                    if sensor=='HR' and sensor_start_unix_t != new_t+cut_at_start_sec-10:
                                        print('Error! %s\'s start time: %d not equal to others: %d, maybe start part been cut' % (sensor_file_path, new_t, sensor_start_unix_t))

                                if sensor != 'IBI':
                                    sensor_fs = int(np.round(sensor_data.iloc[1][0]))
                                    if sensor == 'HR':
                                        sensor_reading = sensor_data.iloc[
                                                         (2 + (cut_at_start_sec - 10) * sensor_fs):, :]
                                    elif sensor == 'EDA':
                                        sensor_reading = sensor_data.iloc[
                                                         (2 + (cut_at_start_sec + eda_shift) * sensor_fs):, :]
                                    else:
                                        sensor_reading = sensor_data.iloc[(2 + cut_at_start_sec * sensor_fs):, :]


                                    wrst_data[sensor] = sensor_reading.values
                                    wrst_data[sensor+'_fs'] = sensor_fs
                                    # check data size to see if they can be divided by sampling rate.
                                    sample_num = wrst_data[sensor].shape[0]
                                    if sample_num>0:
                                        dur = float(sample_num) / sensor_fs
                                        #print('%s duration %f'%(sensor,dur))
                                    else:
                                        print(str('Error! %s has not enough data!' % (sensor_file_path)))
                                        dur = 0
                                    dur_min = min(dur_min, int(dur))
                                else: # not sampling for IBI, it has accumulated time directly.
                                    sensor_fs = -1
                                    wrst_data[sensor + '_fs'] = sensor_fs
                                    sensor_reading = sensor_data.iloc[1:, :]
                                    ibi_data = sensor_reading.values
                                    ibi_data[:,0] = ibi_data[:,0] - cut_at_start_sec
                                    wrst_data[sensor] = ibi_data
                                    sample_num = wrst_data[sensor].shape[0]
                            #print('min duration %d' % (dur_min))

                            if dur_min>0:
                                wrst_data_dict = {'location': wrst_data_dir, 'date': date_dir}
                                wrst_data_dict['wrst_data_index'] = wrst_data_index
                                wrst_data_dict['start_t'] = get_datetime(sensor_start_unix_t)
                                wrst_data_dict['end_t'] = get_datetime(sensor_start_unix_t + dur_min)
                                wrst_data_dict['duration'] = dur_min
                                wrst_data_dict['start_unix_t'] = sensor_start_unix_t
                                wrst_data_dict['end_unix_t'] = sensor_start_unix_t + dur_min

                                wrst_data_dict['tag_unix_t'] = wrst_data['tag_unix_t']
                                # cut the data to meet the minimum durations
                                for sensor in sensors:
                                    if sensor != 'IBI' and wrst_data[sensor].size >0:
                                        wrst_data_dict[sensor] = wrst_data[sensor][0:wrst_data[sensor+'_fs'] *dur_min,:]
                                        wrst_data_dict[sensor + '_fs'] = wrst_data[sensor+'_fs']
                                    else:
                                        wrst_data_dict[sensor] = wrst_data[sensor]
                                        wrst_data_dict[sensor + '_fs'] = wrst_data[sensor + '_fs']

                                wrst_data_index+=1

                                wrst_data_dicts.append(dict(wrst_data_dict))
                            else:
                                print(str('Error! %s all sensors have no valid data' % (full_wrst_data_dir)))

                        else:
                            print('Warning! Not expected folder name: %s' % full_wrst_data_dir)

                    # delete all the zip files
                    shutil.rmtree(zip_path, ignore_errors=True)

                else:
                    print(str('Error! %s has wrong date folder' % (full_date_dir)))


            # create patient pickle patient_szr_num_per_test_date_file and dictionary
            wrst_file_name = os.path.join(wrst_raw_data_dir, dir + '.pkl')
            if os.path.exists(wrst_file_name):
                os.remove(wrst_file_name)

            if len(wrst_data_dicts)>0:
                #start = time.time()
                pickling_on = open(wrst_file_name, "wb")
                pickle.dump(wrst_data_dicts, pickling_on)
                pickling_on.close()
                #end = time.time()
                #print('save picke spend %f' % (end - start))






