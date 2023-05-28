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
    check wristband data quality from RedCap database
Usage:
     Please find it out by run: chk_wrst_data.py -h
'''

# from __future__ import print_function
import os
import sys

print('Current working path is %s' % str(os.getcwd()))
sys.path.insert(0, os.getcwd())

import argparse
from redcap import Project
from redcap_lib import *
from constants import *
from datetime import datetime
from utils.common_func import get_unix_time
from utils.common_func import get_immediate_subdirectories
from utils.common_func import get_datetime
from read_wrist_id import *
# from goto import with_goto

import platform
from pathlib import Path

#@with_goto
def chk_wrst_data_1_patient(project, patient_id, args):

    # wrst_data_root_dir, patient_id, start_timing_err_thre, end_timing_err_thre, wrst_dur_thre, zip_flag

    wrst_data_root_dir = args.path
    start_timing_err_thre = args.start_timing_err_thre
    end_timing_err_thre = args.end_timing_err_thre
    wrst_dur_thre = args.wrst_dur_thre

    events = project.events

    ids_of_interest = ['redcap_event_name', patient_id]
    patient_data_all = project.export_records(records=ids_of_interest)
    # print(patient_data_list)
    if not patient_data_all:
        print('Error! No data was found. Please check your patient ID "%s"' % patient_id)
        return

    first_enroll_age = patient_data_all[0][first_enroll_age_field]
    first_enroll_date = patient_data_all[0][first_enroll_date_field]

    # initialise wristband placement data dictionary
    wrst_placement = {}

    # read wrist band id configuration
    wrst_id_dict = read_wrist_id('data_collection/wristband_id.txt')

    # extract each event's data
    for event in events:
        patient_data_list = get_events_data(patient_data_all, event)

        if not patient_data_list:  # no test data found
            continue

        unique_event_name = event['unique_event_name']
        event_name = event['event_name']

        for patient_data in patient_data_list:

            summary = []

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']

            # update age for each enrollment
            if redcap_repeat_instrument == '' and redcap_repeat_instance == '':
                try:
                    # convert to mm.dd.yyyy
                    enroll_date = patient_data[enroll_date_field]
                    enroll_date_t = datetime.strptime(enroll_date, "%Y-%m-%d")
                    first_enroll_date_t = datetime.strptime(first_enroll_date, "%Y-%m-%d")
                    first_enroll_age_n = float(first_enroll_age)

                    if first_enroll_date_t > enroll_date_t:
                        print('Err! Patient "%s"\'s Event: "%s" first enroll date: %s is later than enroll date: %s' % (
                            patient_id, event_name, first_enroll_date, enroll_date))
                    else:
                        difference_in_days = (enroll_date_t - first_enroll_date_t).days
                        enroll_age = difference_in_days / 365 + first_enroll_age_n

                        to_import_dict = {}
                        to_import_dict['redcap_event_name'] = unique_event_name
                        to_import_dict['redcap_repeat_instrument'] = redcap_repeat_instrument
                        to_import_dict['redcap_repeat_instance'] = redcap_repeat_instance
                        to_import_dict['study_id'] = patient_id
                        to_import_dict[enroll_age_field] = "%.2f" % enroll_age  # str(enroll_age).format("%3.2f")

                        # to_import_dicts = [{'study_id': 'C210', 'redcap_repeat_instance': 1, 'err_per_sec': '5'}]
                        to_import_dicts = [to_import_dict]
                        response = project.import_records(to_import_dicts)
                        if response['count'] == 0:
                            print('update record failed')

                except:
                    print(
                        'ErrCode%d! Patient "%s"\'s Event: "%s" sth wrong in first_enroll_date: %s, first_enroll_age: %s or enroll_date: %s' % (
                            PTS_NO_TEST_DATE, patient_id, event_name, first_enroll_date, first_enroll_age, enroll_date))
                    # continue

            if redcap_repeat_instrument == wrst_place_instru:

                wrst_usage = 0  # 0: data not used; 1: used

                # 1, Ideal case (No Timing Info)
                # 2, With Start Timing Adjust
                # 3, With Start/End Timing Adjust
                timing_case = 1  # by default will be ideal case

                # 0, No raw data
                # 1, Raw data too short
                # 2, Missing EEG onset/offset definition
                # 3, Not used for other reasons
                not_used_reason = 3  # by default other reasons

                # get wristband placement location
                wrst_loc_idx = patient_data[wrst_location_field]

                # didn't indicate the wristband location
                if not wrst_loc_idx:
                    print(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" didn\'t indicate wristband location' % (
                        WRST_NO_LOCATION, patient_id, event_name, redcap_repeat_instance))
                    summary.append(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" didn\'t indicated wristband location' % (
                        WRST_NO_LOCATION, patient_id, event_name, redcap_repeat_instance))
                    not_used_reason = 0
                    upload_wrst_log(project, patient_id, unique_event_name, redcap_repeat_instrument, redcap_repeat_instance,
                                    wrst_usage, not_used_reason, summary)
                    continue

                wrst_loc = wrst_loc_list[int(wrst_loc_idx) - 1].lower()

                # get wristband placement/removal time
                wrst_on = patient_data[wrst_on_field]
                wrst_off = patient_data[wrst_off_field]

                try:
                    # convert to mm.dd.yyyy
                    if wrst_on =='':
                        wrst_on_date =  patient_data[wrst_on_date_field]

                        if wrst_on_date == '':
                            print(
                                'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no placement datetime and date' % (
                                    PTS_WRONG_PLACE_REMOVAL_TIME,
                                    patient_id, event_name, redcap_repeat_instance))
                            summary.append(
                                'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no placement datetime and date' % (
                                    PTS_WRONG_PLACE_REMOVAL_TIME,
                                    patient_id, event_name, redcap_repeat_instance))

                            continue

                        wrst_on = wrst_on_date +' 23:59'
                        print(
                            'Info: Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no placement datetime and been allocated a dummy time %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_on))
                        summary.append(
                            'Info: Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no placement datetime and been allocated a dummy time %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_on))

                    if wrst_off =='':
                        wrst_off_date =  patient_data[wrst_off_date_field]
                        if wrst_off_date == '':
                            print(
                                'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no removal datetime and date' % (
                                    PTS_WRONG_PLACE_REMOVAL_TIME,
                                    patient_id, event_name, redcap_repeat_instance))
                            summary.append(
                                'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no removal datetime and date' % (
                                    PTS_WRONG_PLACE_REMOVAL_TIME,
                                    patient_id, event_name, redcap_repeat_instance))
                            continue

                        wrst_off = wrst_off_date +' 00:00'
                        print(
                            'Info: Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no removal datetime and been allocated a dummy time %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_off))
                        summary.append(
                            'Info: Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" has no removal datetime and been allocated a dummy time %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_off))

                    wrst_on_t = datetime.strptime(wrst_on, "%Y-%m-%d %H:%M")
                    wrst_placement_date = wrst_on_t.strftime("%m.%d.%Y")

                    wrst_off_t = datetime.strptime(wrst_off, "%Y-%m-%d %H:%M")

                    if wrst_off != invalid_t and wrst_on != invalid_t and wrst_off_t < wrst_on_t:
                        print('ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" placement: %s is later than removal: %s' % (PTS_WRONG_PLACE_REMOVAL_TIME,
                            patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))
                        summary.append('ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" placement: %s is later than removal: %s' % (PTS_WRONG_PLACE_REMOVAL_TIME,
                            patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))

                    if wrst_loc in wrst_placement:
                        wrst_placement[wrst_loc].append((wrst_on_t, wrst_off_t, event_name, redcap_repeat_instance))
                    else:
                        wrst_placement[wrst_loc] = [(wrst_on_t, wrst_off_t, event_name, redcap_repeat_instance)]

                except:
                    print(
                        'ErrCode%d! Patient: "%s"\'s Event: "%s" Wristband Instance: "%s" has wrong or empty placement date: %s or removal date: %s' % (
                            PTS_NO_TEST_DATE, patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))
                    summary.append(
                        'ErrCode%d! Patient: "%s"\'s Event: "%s" Wristband Instance: "%s" has wrong or empty placement date: %s or removal date: %s' % (
                            PTS_NO_TEST_DATE, patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))

                wrst_date_dir = os.path.join(wrst_data_root_dir, patient_id, wrst_placement_date)

                # signal downloaded or not
                sig_downloaded = int(patient_data[wrst_download_flag_field])
                if sig_downloaded == 0:
                    print(
                        'Patient: "%s" Event: "%s" Wristband Instance: "%s" signal not downloaded for "%s" under: %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_loc,
                            wrst_date_dir))
                    summary.append(
                        'Patient: "%s" Event: "%s" Wristband Instance: "%s" signal not downloaded for "%s" under: %s' % (
                            patient_id, event_name, redcap_repeat_instance, wrst_loc,
                            wrst_date_dir))
                    not_used_reason = 0
                    upload_wrst_log(project, patient_id, unique_event_name, redcap_repeat_instrument,
                                    redcap_repeat_instance,
                                    wrst_usage, not_used_reason, summary)
                    continue

                # didn't find corresponding left/right sensor folder
                if not os.path.isdir(wrst_date_dir):
                    print('ErrCode%d! Patient "%s" Event: "%s" Wristband Instance: "%s" has no raw data folder: %s' % (
                        WRST_LOC_FOLDER_ERR, patient_id,event_name, redcap_repeat_instance, wrst_date_dir))

                    summary.append('ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" has no raw data folder: %s' % (
                        WRST_LOC_FOLDER_ERR, patient_id, event_name, redcap_repeat_instance, wrst_date_dir))
                    not_used_reason = 0
                    upload_wrst_log(project, patient_id, unique_event_name, redcap_repeat_instrument, redcap_repeat_instance,
                                    wrst_usage, not_used_reason, summary)

                    continue

                ####################################################################################################################
                # check if the raw data exist
                ####################################################################################################################

                # there could be multiple left/right folders
                wrst_data_dirs = get_immediate_subdirectories(wrst_date_dir)  # left xxx or right xxx

                wrst_data_found = False
                for wrst_data_dir in sorted(wrst_data_dirs):
                    if wrst_data_dir.startswith(wrst_loc):
                        wrst_path = os.path.join(wrst_date_dir, wrst_data_dir)

                        # check if zip file name matches with wrist band id
                        zip_found = True
                        if args.zip == 1:
                            files = os.listdir(wrst_path)
                            for filename in sorted(files):
                                if filename.endswith('.zip') and os.path.isfile(
                                        os.path.join(wrst_path, filename)):
                                    zip_found = False

                                    wrst_id_idx = patient_data[wrst_id_field]
                                    if wrst_id_idx == '':
                                        print(
                                            'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" didn\'t specify wristband ID' % (
                                                WRST_WRONG_ZIP_FILE_ID, patient_id, event_name, redcap_repeat_instance))
                                        summary.append(
                                            'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" didn\'t specify wristband ID' % (
                                                WRST_WRONG_ZIP_FILE_ID, patient_id, event_name, redcap_repeat_instance))
                                        break
                                    wrst_id_list = wrst_id_dict[str(wrst_id_idx)]

                                    for wrst_id in wrst_id_list:
                                        if wrst_id in filename:
                                            zip_found = True
                                            break
                                    if not zip_found:
                                        print(
                                            'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" zip file name "%s" not match any wristband ID' % (
                                                WRST_WRONG_ZIP_FILE_ID, patient_id, event_name, redcap_repeat_instance, filename))
                                        summary.append(
                                            'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" zip file name "%s" not match any wristband ID' % (
                                                WRST_WRONG_ZIP_FILE_ID, patient_id, event_name, redcap_repeat_instance,
                                                filename))

                        wrst_data_found = True
                        if not zip_found:
                            wrst_data_found = False
                        # print('Patient: "%s" found raw data folder: %s' % (patient_id, wrst_path))

                if not wrst_data_found:
                    print(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" has no raw data folder for "%s" under: %s' % (
                            WRST_LOC_FOLDER_ERR, patient_id, event_name, redcap_repeat_instance, wrst_loc,
                            wrst_date_dir))
                    summary.append(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" has no raw data folder for "%s" under: %s' % (
                            WRST_LOC_FOLDER_ERR, patient_id, event_name, redcap_repeat_instance, wrst_loc,
                            wrst_date_dir))
                    not_used_reason = 0
                    upload_wrst_log(project, patient_id, unique_event_name, redcap_repeat_instrument, redcap_repeat_instance,
                                    wrst_usage, not_used_reason, summary)
                    continue

                summary, eeg_start_ut, eeg_end_ut = get_eeg_start_end_btn_press_ut(patient_data, patient_id, event_name, redcap_repeat_instance, summary)

                # wristband time/duration information
                total_dur, wrst_start_ut, wrst_end_ut, wrst_btn_prs_start_ut, wrst_btn_prs_start_t, wrst_btn_prs_end_ut, wrst_btn_prs_end_t = get_wrst_time_info(
                    wrst_date_dir, wrst_loc, eeg_start_ut, eeg_end_ut, args)

                # if wrst_start_ut is far away from wristband placement date, it could be a wrong signal.
                wrst_on_ut = get_unix_time(str(wrst_on_t),"%Y-%m-%d %H:%M:%S")
                wrst_start_t = get_datetime(wrst_start_ut, "%Y-%m-%d %H:%M:%S")
                offset_ut = wrst_start_ut - wrst_on_ut
                if offset_ut < -6*3600: # too early
                    print(
                        'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start: "%s" too earlier than wristband placement time: "%s"' % (
                            WRST_START_TOO_EARLY, patient_id, event_name, redcap_repeat_instance,
                            wrst_start_t, wrst_on_t))
                    summary.append(
                        'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start: "%s" too earlier than wristband placement time: "%s"' % (
                            WRST_START_TOO_EARLY, patient_id, event_name, redcap_repeat_instance,
                            wrst_start_t, wrst_on_t))
                elif offset_ut > 24*3600: # too late
                    print(
                        'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start: "%s" too later than wristband placement time: "%s"' % (
                            WRST_START_TOO_LATE, patient_id, event_name, redcap_repeat_instance,
                            wrst_start_t, wrst_on_t))
                    summary.append(
                        'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start: "%s" too later than wristband placement time: "%s"' % (
                            WRST_START_TOO_LATE, patient_id, event_name, redcap_repeat_instance,
                            wrst_start_t, wrst_on_t))

                ####################################################################################################################
                # update wristband data
                ####################################################################################################################
                # label .update_wrst_data_label

                to_import_dict = {}
                to_import_dict['redcap_event_name'] = unique_event_name
                to_import_dict['redcap_repeat_instrument'] = redcap_repeat_instrument
                to_import_dict['redcap_repeat_instance'] = redcap_repeat_instance
                to_import_dict['study_id'] = patient_id

                valid_start_timing_flag  = False
                valid_end_timing_flag = False

                if wrst_btn_prs_start_ut != -1 and eeg_start_ut != -1:
                    start_timing_err = wrst_btn_prs_start_ut - eeg_start_ut
                    to_import_dict[start_timing_err_field] = str(start_timing_err)
                    if abs(start_timing_err) > start_timing_err_thre:
                        print(
                            'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start_timing_err: %4.2f is too large' % (
                                WRST_EEG_START_TIMING_ERR, patient_id, event_name, redcap_repeat_instance,
                                start_timing_err))
                        summary.append(
                            'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" start_timing_err: %4.2f is too large' % (
                                WRST_EEG_START_TIMING_ERR, patient_id, event_name, redcap_repeat_instance,
                                start_timing_err))
                    else:
                        valid_start_timing_flag = True
                else:
                    to_import_dict[start_timing_err_field] = '99999999'

                if wrst_btn_prs_end_ut != -1 and eeg_end_ut != -1:
                    end_timing_err = wrst_btn_prs_end_ut - eeg_end_ut
                    to_import_dict[end_timing_err_field] = str(end_timing_err)
                    if abs(end_timing_err) > end_timing_err_thre:
                        print(
                            'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" end_timing_err: %4.2f is too large' % (
                                WRST_EEG_END_TIMING_ERR, patient_id, event_name, redcap_repeat_instance,
                                end_timing_err))
                        summary.append(
                            'WarnCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" end_timing_err: %4.2f is too large' % (
                                WRST_EEG_END_TIMING_ERR, patient_id, event_name, redcap_repeat_instance,
                                end_timing_err))
                    else:
                        valid_end_timing_flag = True
                else:
                    to_import_dict[end_timing_err_field] = '99999999'

                if valid_start_timing_flag and valid_end_timing_flag:
                    timing_case = 3
                    timing_drift = (wrst_btn_prs_end_ut - wrst_btn_prs_start_ut) - (eeg_end_ut - eeg_start_ut)
                    to_import_dict[timing_drift_field] = str(timing_drift)
                    err_per_sec = timing_drift / (eeg_end_ut - eeg_start_ut)
                    to_import_dict[err_per_sec_field] = str(err_per_sec)

                elif valid_start_timing_flag:
                    timing_case = 2
                    #timing_drift = -13 # offline default value
                    #to_import_dict[timing_drift_field] = str(timing_drift)
                    #err_per_sec = timing_drift / 86400 # for 24 Hours
                    #to_import_dict[err_per_sec_field] = str(err_per_sec)
                    to_import_dict[timing_drift_field] = '99999999'
                    to_import_dict[err_per_sec_field] = '99999999'
                else:
                    timing_case = 1
                    to_import_dict[timing_drift_field] = '99999999'
                    to_import_dict[err_per_sec_field] = '99999999'


                # by default >1 hr will be necessary
                if total_dur >= wrst_dur_thre:
                    wrst_usage= 1
                else:
                    not_used_reason = 1

                if wrst_btn_prs_start_t != '':
                    to_import_dict[wrst_btn_prs_start_t_field] = wrst_btn_prs_start_t
                else:
                    to_import_dict[wrst_btn_prs_start_t_field] = '1900-01-01 00:00:00'

                if wrst_btn_prs_end_t != '':
                    to_import_dict[wrst_btn_prs_end_t_field] = wrst_btn_prs_end_t
                else:
                    to_import_dict[wrst_btn_prs_end_t_field] = '1900-01-01 00:00:00'

                to_import_dict[wrst_dur_field] = str(total_dur)

                try:
                    to_import_dict[wrst_start_t_field] = get_datetime(wrst_start_ut, "%Y-%m-%d %H:%M:%S")
                except:
                    to_import_dict[wrst_start_t_field] = '1900-01-01 00:00:00'
                try:
                    to_import_dict[wrst_end_t_field] = get_datetime(wrst_end_ut, "%Y-%m-%d %H:%M:%S")
                except:
                    to_import_dict[wrst_end_t_field] = '1900-01-01 00:00:00'

                to_import_dict[wrst_case_field] = timing_case
                to_import_dict[wrst_not_use_reasons_field] = not_used_reason
                to_import_dict[wrst_usage_field] = wrst_usage

                if summary==[]:
                    summary.append('All Passed!')

                to_import_dict[wrst_log_field] = '\n'.join(summary)

                # to_import_dicts = [{'study_id': 'C210', 'redcap_repeat_instance': 1, 'err_per_sec': '5'}]
                to_import_dicts = [to_import_dict]
                response = project.import_records(to_import_dicts)
                if response['count'] == 0:
                    print('update record failed')


    # end of for event in events:
    # print(wrst_placement)
    for loc in wrst_placement:
        loc_wrst_placement = wrst_placement[loc]
        # print('location %s, %s'%(loc,loc_wrst_placement))
        sorted_wrst_placement = sorted(loc_wrst_placement, key=lambda tup: tup[0])
        for ii in range((len(sorted_wrst_placement) - 1)):
            pre_removal = sorted_wrst_placement[ii][1]  # removal date
            next_placement = sorted_wrst_placement[ii + 1][0]

            # no overlap allowed
            if next_placement < pre_removal:
                pre_placement = sorted_wrst_placement[ii][0]  # removal date
                next_removal = sorted_wrst_placement[ii + 1][1]

                pre_event = sorted_wrst_placement[ii][2]
                next_event = sorted_wrst_placement[ii + 1][2]
                pre_inst = sorted_wrst_placement[ii][3]
                next_inst = sorted_wrst_placement[ii + 1][3]
                print(
                    'WarnCode%d! Patient "%s"\'s Event: "%s" Wristband Instance: "%s": (%s ~ %s) is overlapped with Event: "%s" instance %s: (%s ~ %s)'
                    % (WRST_OVERLAP, patient_id, pre_event, pre_inst, pre_placement, pre_removal,
                       next_event, next_inst, next_placement, next_removal))


def chk_wrst_data(project, args):
    #wrst_data_root_dir, patient_id, start_timing_err_thre, end_timing_err_thre, wrst_dur_thre, zip_flag

    patient_id = args.patient_id

    patient_id_list = get_unique_patient_id_for_ibm(project, export_flag_field, ibm_flag_idx)
    print('Patient ID List = %s' % patient_id_list)

    if patient_id:
        if patient_id.upper() in patient_id_list:
            print('\nChecking patient_id=%s \'s wristband Data ...' % patient_id)
            chk_wrst_data_1_patient(project, patient_id, args)
        else:
            print('Err! patient_id=%s doesn\'t exist in the database' % patient_id)
    else:
        for idx, patient_id in enumerate(patient_id_list):
            print('\n%d/%d: Checking patient_id=%s \'s wristband Data ...' % (
                idx + 1, len(patient_id_list), patient_id))
            chk_wrst_data_1_patient(project, patient_id, args)

# usage
# python3 data_collection/chk_wrst_data.py --api_key EF8B5CABBCCEE7C0B007F0F688AD8626 --path "/Users/jbtang/datasets/bch/new_procedure_data" --zip 1 --zip_path "/Users/jbtang/Documents/bch_unzip_file/" --patient_id C189

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check Wristband Raw Data Quality')

    parser.add_argument('--api_url', type=str, default='https://redcap.tch.harvard.edu/redcap_edc/api/',
                        help='Redcap API\'s url')

    parser.add_argument('--api_key', type=str, default='',
                       help='Redcap API\'s key')

    if platform.system() == 'Linux':
        parser.add_argument('--path', type=str, default='/bigdata/datasets/bch/REDCap_202109',
            help='wrst_data_root_dir to wristband raw data')
    elif platform.system() == 'Darwin':
        parser.add_argument('--path', type=str, default=os.path.join(Path.home(),'datasets/bch/REDCap_202109'),
                            help='wrst_data_root_dir to wristband raw data')
    else:
        print('Unknown OS platform %s' % platform.system())
        exit()

    parser.add_argument('--patient_id', type=str,
                        help='format: Cxxx. If not specified, check all patients')
    parser.add_argument('--start_timing_err_thre', type=int, default='20',
                        help='Maximum tolerable timing error at the beginning, by default, 20s')
    parser.add_argument('--end_timing_err_thre', type=int, default='50',
                        help='Maximum tolerable timing error at the end, by default, 50s')
    parser.add_argument('--wrst_dur_thre', type=int, default='3600',
                        help='minimum wristband data duration')

    parser.add_argument('--zip', type=int, default=1,
                        help='enable unzip and zip wristband signal')

    parser.add_argument('--zip_path', type=str, default='temp_files/',
                        help='temporal path to save unzipped wristband raw data')

    args = parser.parse_args()

    try:
        project = Project(args.api_url, args.api_key)
    except:
        print('Fail to connect RedCap, please make sure you have correct--api_url and --api_key')
        exit()


    # args.start_timing_err_thre = 0
    # args.end_timing_err_thre = 0
    # args.patient_id = 'C242'

    chk_wrst_data(project, args)

    print('\nCheck Wristband Data is done')
