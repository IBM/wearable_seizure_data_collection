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
    Library to access Redcap database
'''

import numpy as np
from utils.common_func import *
import os
import pandas as pd
from data_collection.constants import *
import zipfile
import shutil


def get_unique_patient_id_for_ibm(project,export_flag_field,ibm_flag_idx):
    fields_of_interest = [export_flag_field]
    patient_ids = project.export_records(fields=fields_of_interest)
    patient_id_list = []
    export_flag_field_ibm = export_flag_field + '___' + str(ibm_flag_idx)
    for patient_id in patient_ids:

        # to check ibm only
        #if patient_id[export_flag_field_ibm] == '1':
        #    patient_id_list.append(patient_id['study_id'])

        # check everyone
        patient_id_list.append(str(patient_id['study_id']).upper())
    return np.unique(patient_id_list)


def get_events_data(patient_data_all,event):
    patient_data_list = []
    for patient_data in patient_data_all:
        if patient_data['redcap_event_name']==event['unique_event_name']:
            patient_data_list.append(patient_data)

    return patient_data_list

def upload_szr_wrst_loc(project, patient_id, event, redcap_repeat_instrument, redcap_repeat_instance, wrst_loc, value):
    # upload log if any
    to_import_dict = {}
    to_import_dict['redcap_event_name'] = event
    to_import_dict['redcap_repeat_instrument'] = redcap_repeat_instrument
    to_import_dict['redcap_repeat_instance'] = redcap_repeat_instance
    to_import_dict['study_id'] = patient_id

    '''
    wrist_loc	                  1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown | 8, Unknown Wrist | 9, Unknown Ankle
    # szr_wrst_loc	0, Not used | 1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown
                # szr_wrst_loc___0	szr_wrst_loc___1	szr_wrst_loc___2	szr_wrst_loc___3	szr_wrst_loc___4	szr_wrst_loc___5	szr_wrst_loc___6	szr_wrst_loc___7					
    '''
    if wrst_loc.lower() == 'not used':
        to_import_dict['szr_wrst_loc___0'] = value
        to_import_dict['szr_wrst_loc___1'] = 0
        to_import_dict['szr_wrst_loc___2'] = 0
        to_import_dict['szr_wrst_loc___3'] = 0
        to_import_dict['szr_wrst_loc___4'] = 0
        to_import_dict['szr_wrst_loc___5'] = 0
        to_import_dict['szr_wrst_loc___6'] = 0
        to_import_dict['szr_wrst_loc___7'] = 0
        to_import_dict['szr_wrst_loc___8'] = 0
        to_import_dict['szr_wrst_loc___9'] = 0

    else:
        to_import_dict['szr_wrst_loc___0'] = 0
        # need to find which wrst_loc matches to below list
        #wrst_loc_list = ['Left Wrist', 'Left Ankle', 'Right Wrist', 'Right Ankle', 'Unk', 'Right Unk', 'Left Unk',
        #                 'Unk wrist', 'Unk ankle']
        if wrst_loc.lower() == 'left wrist':
            to_import_dict['szr_wrst_loc___1'] = value
        elif wrst_loc.lower() == 'left ankle':
            to_import_dict['szr_wrst_loc___2'] = value
        elif wrst_loc.lower() == 'right wrist':
            to_import_dict['szr_wrst_loc___3'] = value
        elif wrst_loc.lower() == 'right ankle':
            to_import_dict['szr_wrst_loc___4'] = value
        elif wrst_loc.lower() == 'unk wrist':
            to_import_dict['szr_wrst_loc___8'] = 1
            #pass
        elif wrst_loc.lower() == 'unk ankle':
            to_import_dict['szr_wrst_loc___9'] = 1
            #pass
        elif wrst_loc.lower() == 'unk':
            to_import_dict['szr_wrst_loc___5'] = value
        elif wrst_loc.lower() == 'right unk':
            to_import_dict['szr_wrst_loc___6'] = value
        elif wrst_loc.lower() == 'left unk':
            to_import_dict['szr_wrst_loc___7'] = value



    to_import_dicts = [to_import_dict]
    response = project.import_records(to_import_dicts)
    if response['count'] == 0:
        print('update record failed')

def upload_eeg_log(project, patient_id, event, redcap_repeat_instrument, redcap_repeat_instance, summary):
    # upload log if any
    to_import_dict = {}
    to_import_dict['redcap_event_name'] = event
    to_import_dict['redcap_repeat_instrument'] = redcap_repeat_instrument
    to_import_dict['redcap_repeat_instance'] = redcap_repeat_instance
    to_import_dict['study_id'] = patient_id

    to_import_dict[szr_log_field] = '\n'.join(summary)

    to_import_dicts = [to_import_dict]
    response = project.import_records(to_import_dicts)
    if response['count'] == 0:
        print('update record failed')


def upload_wrst_log(project, patient_id, event, redcap_repeat_instrument, redcap_repeat_instance, wrst_usage, not_used_reason, summary):
    # upload log if any
    to_import_dict = {}
    to_import_dict['redcap_event_name'] = event
    to_import_dict['redcap_repeat_instrument'] = redcap_repeat_instrument
    to_import_dict['redcap_repeat_instance'] = redcap_repeat_instance
    to_import_dict['study_id'] = patient_id

    to_import_dict[wrst_not_use_reasons_field] = not_used_reason
    to_import_dict[wrst_usage_field] = wrst_usage
    to_import_dict[wrst_log_field] = '\n'.join(summary)

    #to_import_dict[wrst_case_field] = 1
    to_import_dict[wrst_btn_prs_start_t_field] = '1900-01-01 00:00:00'
    to_import_dict[wrst_btn_prs_end_t_field] = '1900-01-01 00:00:00'
    to_import_dict[wrst_dur_field] = '99999999'
    to_import_dict[start_timing_err_field] = '99999999'
    to_import_dict[end_timing_err_field] = '99999999'
    to_import_dict[timing_drift_field] = '99999999'
    to_import_dict[err_per_sec_field] = '99999999'

    to_import_dicts = [to_import_dict]
    response = project.import_records(to_import_dicts)
    if response['count'] == 0:
        print('update record failed')

# sometimes, there are multiple left/right wrst folders corresponding 1 PTS.
# output a list of wrst_start_t, wrst_end_t, total duraton, wrst_btn_prs_start_t(tags_uts), wrst_btn_prs_end_t(tags_end_uts)
def get_wrst_time_info(wrst_full_date_dir, wrst_loc, eeg_start_ut, eeg_end_ut, args):
    if args.zip == 0:
        zip_flag = False
    else:
        zip_flag = True
        zip_path = args.zip_path
        shutil.rmtree(zip_path, ignore_errors=True)

        # # Delete everything reachable from the directory named in 'top',
        # # assuming there are no symbolic links.
        # # CAUTION:  This is dangerous!  For example, if top == '/', it
        # # could delete all your disk files.
        # import os
        # for root, dirs, files in os.walk(zip_path, topdown=False):
        #     for name in files:
        #         os.remove(os.path.join(root, name))
        #     for name in dirs:
        #         os.rmdir(os.path.join(root, name))

        os.makedirs(zip_path, 0o777, True)
        # try to delete unzipped file
        # os.remove(os.path.join(zip_path, 'ACC.csv'))
        # os.remove(os.path.join(zip_path, 'BVP.csv'))
        # os.remove(os.path.join(zip_path, 'EDA.csv'))
        # os.remove(os.path.join(zip_path, 'HR.csv'))
        # os.remove(os.path.join(zip_path, 'IBI.csv'))
        # os.remove(os.path.join(zip_path, 'tags.csv'))
        # os.remove(os.path.join(zip_path, 'TEMP.csv'))
        # os.remove(os.path.join(zip_path, 'info.txt'))

        # shutil.rmtree(os.path.join(zip_path, 'ACC.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'BVP.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'EDA.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'HR.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'IBI.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'tags.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'TEMP.csv'), ignore_errors=True)
        # shutil.rmtree(os.path.join(zip_path, 'info.txt'), ignore_errors=True)

    # init with invalid time
    tags_start_uts = []
    tags_end_uts = []
    sensor_start_uts = []
    sensor_end_uts = []
    # wrst_selected_data_dirs = []
    total_dur = 0 # seconds

    wrst_data_dirs = get_immediate_subdirectories(wrst_full_date_dir)  # left xxx or right xxx

    # since there could be multiple left/right folders, we will generate a list of tags_uts
    # then find the earliest positive value, compare to eeg button press time to see if it is close enough
    for wrst_data_dir in sorted(wrst_data_dirs):

        # check the format is correct
        full_wrst_data_dir = os.path.join(wrst_full_date_dir, wrst_data_dir)
        if wrst_data_dir.startswith(wrst_loc):

            # try unzip file here
            if zip_flag:
                zip_found = False
                files = os.listdir(full_wrst_data_dir)
                for filename in sorted(files):
                    if filename.endswith('.zip') and os.path.isfile(os.path.join(full_wrst_data_dir, filename)):
                        zipfile.ZipFile(os.path.join(full_wrst_data_dir, filename)).extractall(zip_path)
                        full_wrst_data_dir = zip_path


                        zip_found = True
                        break # only extract first zip file

            # wrst_selected_data_dirs.append(wrst_data_dir)
            # print(full_wrst_data_dir)
            full_tag_file_dir = os.path.join(full_wrst_data_dir, 'tags.csv')
            try:
                tags_data = pd.read_csv(full_tag_file_dir, header=None)
                tags_start_uts.append(float(tags_data.iloc[0]))
                tags_end_uts.append(float(tags_data.iloc[len(tags_data) - 1]))
            except:
                tags_start_uts.append(-1)
                tags_end_uts.append(-1)
                # print('Warning! %s is empty or not exist!' % full_tag_file_dir)
                pass

            # get wrst start unix t from TEMP 1st line, since it is smallest and most stable
            # check if patient_szr_num_per_test_date_file exists
            sensor_file_path = os.path.join(full_wrst_data_dir, 'TEMP.csv')
            try:
                sensor_data = pd.read_csv(sensor_file_path, header=None)
                sensor_start_uts.append(float(sensor_data.iloc[0][0]))
                sensor_fs = int(np.round(sensor_data.iloc[1][0]))
                sensor_dur = (sensor_data.shape[0] - 2) / sensor_fs
                total_dur += sensor_dur
                sensor_end_uts.append(float(sensor_data.iloc[0][0]) + sensor_dur)
            except:
                sensor_fs = -1
                sensor_data = pd.DataFrame()
                print('ErrCode%d! %s is empty or not exist!' % (WRST_NO_START_TIME, sensor_file_path))

            # # try detele unzip file here
            # if zip_flag and zip_found:
            #     files=os.listdir(full_wrst_data_dir)
            #     for filename in files:
            #         if not filename.endswith('.zip') and os.path.isfile(os.path.join(full_wrst_data_dir, filename)):
            #             file_full_path = os.path.join(full_wrst_data_dir, filename)
            #             #os.chmod(file_full_path, 0o777)
            #             os.remove(file_full_path)


    wrst_btn_prs_start_t = ''
    wrst_btn_prs_end_t = ''
    #####################################################################Î##############################################
    # Find wristband  start button press time
    ####################################################################################################################
    wrst_btn_prs_start_ut = get_wrst_btn_press_ut(tags_start_uts, eeg_start_ut)
    if wrst_btn_prs_start_ut != -1:
        wrst_btn_prs_start_t = get_datetime(wrst_btn_prs_start_ut, "%Y-%m-%d %H:%M:%S")

    #####################################################################Î##############################################
    # Find wristband end button press time
    ####################################################################################################################
    wrst_btn_prs_end_ut = get_wrst_btn_press_ut(tags_end_uts, eeg_end_ut)
    if wrst_btn_prs_end_ut != -1:
        wrst_btn_prs_end_t = get_datetime(wrst_btn_prs_end_ut, "%Y-%m-%d %H:%M:%S")

    wrst_end_ut = max(sensor_end_uts)
    wrst_start_ut = min(sensor_start_uts)
    #return  total_dur, sensor_start_uts, sensor_end_uts, tags_start_uts, tags_end_uts
    return total_dur, wrst_start_ut, wrst_end_ut, wrst_btn_prs_start_ut, wrst_btn_prs_start_t, wrst_btn_prs_end_ut, wrst_btn_prs_end_t


    # # get tags_start_ut
    # if max(tags_start_uts) == -1:# not tag was found
    #     tags_start_ut = -1
    # else:
    #     # according to meeting in Sep5, 2019, use closest start time as start!
    #     diff_ut = [abs(x - eeg_start_ut) for x in tags_start_uts]
    #     min_diff_idx = diff_ut.index(min(diff_ut))
    #     if len(tags_start_uts) > 1: #more than 1 records
    #         print('%s/%s has %d records, using %s\'s as wristband start button press time, min difference: %4.2f ' % (
    #             wrst_full_date_dir, wrst_loc, len(tags_start_uts), wrst_selected_data_dirs[min_diff_idx], min(diff_ut)))
    #     tags_start_ut = tags_start_uts[min_diff_idx]
    #
    # # get tags_end_uts
    # if max(tags_end_uts) == -1:# not tag was found
    #     tags_end_ut = -1
    # else:
    #     # according to meeting in Sep5, 2019, use closest end time as end!
    #     diff_ut = [abs(x - eeg_end_ut) for x in tags_end_uts]
    #     min_diff_idx = diff_ut.index(min(diff_ut))
    #     if len(tags_end_uts) > 1: #more than 1 records
    #         print('%s/%s has %d records, using %s\'s as wristband end button press time, min difference: %4.2f ' % (
    #             wrst_full_date_dir, wrst_loc, len(tags_start_uts), wrst_selected_data_dirs[min_diff_idx], min(diff_ut)))
    #     tags_end_ut = tags_end_uts[min_diff_idx]


# when we have multiple tag t, according to meeting in Sep5, 2019, use closest start time as start!
def get_wrst_btn_press_ut(tags_uts, eeg_ut):
    # get tags_start_ut
    if max(tags_uts) == -1 or eeg_ut == -1:# not tag was found
        tags_start_ut = -1
    else:
        diff_ut = [abs(x - eeg_ut) for x in tags_uts]
        min_diff_idx = diff_ut.index(min(diff_ut))
        tags_start_ut = tags_uts[min_diff_idx]

    return tags_start_ut

def get_eeg_start_end_btn_press_ut(patient_data, patient_id, event_name, redcap_repeat_instance, summary):
    # initialise the variables
    eeg_start_btn_press_ut = -1
    eeg_end_btn_press_ut = -1

    ####################################################################################################################
    # Find EEG start time
    ####################################################################################################################
    start_timing_sync_src_flag_field_str = patient_data[start_timing_sync_src_flag_field]

    # format: 2017-07-10 14:45:51
    eeg_start_t_str = ''
    if start_timing_sync_src_flag_field_str == '1':  # video
        eeg_start_t_str = patient_data[video_btn_prs_start_t_field]
    elif start_timing_sync_src_flag_field_str == '2':  # eeg
        eeg_start_t_str = patient_data[eeg_btn_prs_start_t_field]
    elif start_timing_sync_src_flag_field_str == '3':
        pass
    else:
        print(
            'Patient: "%s" Event: "%s" Wristband Instance: "%s" \'s EEG Start timing sync source not specified' % (
                patient_id, event_name, redcap_repeat_instance))
        summary.append(
            'Patient: "%s" Event: "%s" Wristband Instance: "%s" \'s EEG Start timing sync source not specified' % (
                patient_id, event_name, redcap_repeat_instance))


    if not eeg_start_t_str == '':
        try:
            # since redcap already check the region, didn't check here
            eeg_start_btn_press_ut = get_unix_time(eeg_start_t_str, "%Y-%m-%d %H:%M:%S")
        except:
            print(
                'Err! Patient: "%s" Event: "%s" Wristband Instance: "%s" has wrong or empty EEG start time: %s' % (
                    patient_id, event_name, redcap_repeat_instance, eeg_start_t_str))
            summary.append(
                'Err! Patient: "%s" Event: "%s" Wristband Instance: "%s" has wrong or empty EEG start time: %s' % (
                    patient_id, event_name, redcap_repeat_instance, eeg_start_t_str))


    ####################################################################################################################
    # Find EEG end time
    ####################################################################################################################
    end_timing_sync_src_flag_field_str = patient_data[end_timing_sync_src_flag_field]

    # format: 2017-07-10 14:45:51
    eeg_end_t_str = ''
    if end_timing_sync_src_flag_field_str == '1':  # video
        eeg_end_t_str = patient_data[video_btn_prs_end_t_field]
    elif end_timing_sync_src_flag_field_str == '2':  # eeg
        eeg_end_t_str = patient_data[eeg_btn_prs_end_t_field]
    elif end_timing_sync_src_flag_field_str == '3':
        pass
    else:
        print(
            'Patient: "%s" Event: "%s" Wristband Instance: "%s" \'s EEG End timing sync source not specified' % (
                patient_id, event_name, redcap_repeat_instance))
        summary.append(
            'Patient: "%s" Event: "%s" Wristband Instance: "%s" \'s EEG End timing sync source not specified' % (
                patient_id, event_name, redcap_repeat_instance))


    if not eeg_end_t_str == '':
        try:
            # since redcap already check the region, didn't check here
            # print('Patient: "%s" EEG Start time %s, EEG End time %s' % (patient_id, eeg_start_t_str, eeg_end_t_str))
            eeg_end_btn_press_ut = get_unix_time(eeg_end_t_str, "%Y-%m-%d %H:%M:%S")
        except:
            print(
                'Err! Patient: "%s" Event: "%s" Wristband Instance: "%s" has wrong or empty EEG end time:  %s' % (
                    patient_id, event_name, redcap_repeat_instance, eeg_end_t_str))
            summary.append(
                'Err! Patient: "%s" Event: "%s" Wristband Instance: "%s" has wrong or empty EEG end time: %s' % (
                    patient_id, event_name, redcap_repeat_instance, eeg_end_t_str))


    return summary, eeg_start_btn_press_ut, eeg_end_btn_press_ut

