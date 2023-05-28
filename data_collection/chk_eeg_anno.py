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
    check EEG annotation data from RedCap database
Usage:
     Please find it out by run: chk_eeg_anno.py -h
'''

from __future__ import print_function

import os
import sys

print('Current working wrst_data_root_dir is %s' % str(os.getcwd()))
sys.path.insert(0, os.getcwd())

import argparse
from redcap import Project
from redcap_lib import *
from constants import *
from utils.common_func import get_unix_time
from utils.common_func import get_datetime
import numpy as np


def chk_eeg_anno_1_patient(project, patient_id):
    events = project.events

    ids_of_interest = ['redcap_event_name', patient_id]
    patient_data_all = project.export_records(records=ids_of_interest)
    if not patient_data_all:
        print('Error! No data was found. Please check your patient ID "%s"' % patient_id)
        return

    # extract each event's data
    for event in events:

        unique_event_name = event['unique_event_name']
        event_name = event['event_name']
        patient_data_list = get_events_data(patient_data_all, event)

        if not patient_data_list:  # no test date found
            continue

        # step 1: find EEG start time and end time by going through all wristbands' EEG start/end time
        # if EEG button press time are not found, use wristband's on/off time to replace

        min_eeg_start_ut = POS_BIG_NUM
        max_eeg_end_ut = 0
        min_wrst_on_ut = POS_BIG_NUM
        max_wrst_off_ut = 0

        for patient_data in patient_data_list:
            summary = []

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']

            if redcap_repeat_instrument == wrst_place_instru:

                wrst_loc_idx = patient_data[wrst_location_field]
                if not wrst_loc_idx:
                    print('ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance %s didn\'t indicate wristband location' % (
                    WRST_NO_LOCATION, patient_id, event_name, redcap_repeat_instance))
                    summary.append(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance %s didn\'t indicate wristband location' % (
                        WRST_NO_LOCATION, patient_id, event_name, redcap_repeat_instance))
                    upload_wrst_log(project, patient_id, unique_event_name, redcap_repeat_instrument,
                                    redcap_repeat_instance,
                                    0, 0, summary)
                    continue

                # get wristband placement/removal time
                wrst_on = patient_data[wrst_on_field]
                wrst_off = patient_data[wrst_off_field]

                try:
                    # convert to mm.dd.yyyy
                    wrst_on_ut = get_unix_time(wrst_on, "%Y-%m-%d %H:%M")
                    wrst_off_ut = get_unix_time(wrst_off, "%Y-%m-%d %H:%M")

                    if wrst_off != invalid_t:
                        max_wrst_off_ut = max(max_wrst_off_ut, wrst_off_ut)
                    if wrst_on != invalid_t:
                        min_wrst_on_ut = min(min_wrst_on_ut, wrst_on_ut)

                    if wrst_off != invalid_t and wrst_on != invalid_t and wrst_off_ut < wrst_on_ut:
                        print(
                            'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" placement: %s is later than removal: %s' % (
                            PTS_WRONG_PLACE_REMOVAL_TIME,
                            patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))
                        summary.append(
                            'ErrCode%d! Patient  "%s"\'s Event: "%s" Wristband Instance: "%s" placement: %s is later than removal: %s' % (
                            PTS_WRONG_PLACE_REMOVAL_TIME,
                            patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))
                except:
                    print(
                        'ErrCode%d! Patient: "%s"\'s Event: "%s" Wristband Instance: "%s" has wrong or empty placement date: %s or removal date: %s' % (
                            PTS_NO_TEST_DATE, patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))
                    summary.append(
                        'ErrCode%d! Patient: "%s"\'s Event: "%s" Wristband Instance: "%s" has wrong or empty placement date: %s or removal date: %s' % (
                            PTS_NO_TEST_DATE, patient_id, event_name, redcap_repeat_instance, wrst_on, wrst_off))

                summary, eeg_start_ut, eeg_end_ut = get_eeg_start_end_btn_press_ut(patient_data, patient_id, event_name, redcap_repeat_instance, summary)
                if eeg_start_ut != -1:
                    min_eeg_start_ut = min(min_eeg_start_ut,eeg_start_ut)
                if eeg_end_ut != -1:
                    max_eeg_end_ut = min(max_eeg_end_ut, eeg_end_ut)

        if min_eeg_start_ut == POS_BIG_NUM: # no valid EEG start button press time was found
            if min_wrst_on_ut == POS_BIG_NUM: # no valid wrst on time was found
                eeg_start_ut = 0
            else:
                eeg_start_ut = min_wrst_on_ut
        else:
            eeg_start_ut = min_eeg_start_ut

        if max_eeg_end_ut == 0:  # no valid EEG start button press time was found
            if max_wrst_off_ut == 0:  # no valid wrst off time was found
                eeg_end_ut = POS_BIG_NUM
            else:
                eeg_end_ut = max_wrst_off_ut
        else:
            eeg_end_ut = max_eeg_end_ut

        # step 2: make sure each eeg annotation is within scope, no overlap, no negative duration

        # first, get all the onset/offset
        eeg_onset_uts = []
        eeg_offset_uts = []
        redcap_repeat_instances = []
        for patient_data in patient_data_list:
            summary = []

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']
            if redcap_repeat_instrument == szr_anno_instru:
                redcap_repeat_instances.append(redcap_repeat_instance)
                eeg_onset_t_str = patient_data[eeg_szr_onset_field]
                eeg_offset_t_str = patient_data[eeg_szr_offset_field]

                try:
                    eeg_onset_ut = get_unix_time(eeg_onset_t_str, "%Y-%m-%d %H:%M:%S")
                    if eeg_offset_t_str != '':
                        eeg_offset_ut = get_unix_time(eeg_offset_t_str, "%Y-%m-%d %H:%M:%S")
                        eeg_dur = eeg_offset_ut - eeg_onset_ut
                    elif patient_data[dura_ltm_avai_field] == '1':
                        eeg_dur = float(patient_data[dura_ltm_field])
                        eeg_offset_ut = eeg_dur + eeg_onset_ut
                    else:
                        print(
                            'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset: %s or offset: %s' % (
                            SZR_WRONG_DUR,
                            patient_id, event_name,
                            redcap_repeat_instance, eeg_onset_t_str, eeg_offset_t_str))
                        summary.append(
                            'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset: %s or offset: %s' % (
                            SZR_WRONG_DUR,
                            patient_id, event_name,
                            redcap_repeat_instance, eeg_onset_t_str, eeg_offset_t_str))

                        upload_eeg_log(project, patient_id, unique_event_name, redcap_repeat_instrument,
                                       redcap_repeat_instance, summary)

                        eeg_onset_uts.append(0)
                        eeg_offset_uts.append(0)

                        continue

                    if eeg_dur < 0:
                        print(
                            'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset/offset/duration time' % (
                            SZR_WRONG_DUR,
                            patient_id, event_name,
                            redcap_repeat_instance))
                        summary.append(
                            'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset/offset/duration time' % (
                            SZR_WRONG_DUR,
                            patient_id, event_name,
                            redcap_repeat_instance))
                        upload_eeg_log(project, patient_id, unique_event_name, redcap_repeat_instrument,
                                       redcap_repeat_instance, summary)

                        eeg_onset_uts.append(0)
                        eeg_offset_uts.append(0)
                        continue

                except:
                    print(
                        'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset/offset/duration time' % (
                        SZR_WRONG_DUR,
                        patient_id, event_name,
                        redcap_repeat_instance))
                    summary.append(
                        'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset/offset/duration time' % (
                        SZR_WRONG_DUR,
                        patient_id, event_name,
                        redcap_repeat_instance))
                    upload_eeg_log(project, patient_id, unique_event_name, redcap_repeat_instrument,
                                   redcap_repeat_instance, summary)

                    eeg_onset_uts.append(0)
                    eeg_offset_uts.append(0)
                    continue

                if eeg_onset_ut < eeg_start_ut:
                    eeg_onset_ut_str = get_datetime(eeg_onset_ut)
                    eeg_start_ut_str = get_datetime(eeg_start_ut)
                    print(
                        'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s"\'s seizure onset time %s is earlier than EEG or wristband start time %s' % (
                            SZR_EARLY_ONSET,
                            patient_id, event_name, redcap_repeat_instance, eeg_onset_ut_str, eeg_start_ut_str))
                    summary.append(
                        'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s"\'s seizure onset time %s is earlier than EEG or wristband start time %s' % (
                            SZR_EARLY_ONSET,
                            patient_id, event_name, redcap_repeat_instance, eeg_onset_ut_str, eeg_start_ut_str))

                if eeg_offset_ut > eeg_end_ut:
                    eeg_offset_ut_str = get_datetime(eeg_offset_ut)
                    eeg_end_ut_str = get_datetime(eeg_end_ut)
                    print(
                        'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s"\'s seizure offset time %s is later than EEG or wristband end time %s' % (
                            SZR_LATE_OFFSET, patient_id, event_name, redcap_repeat_instance, eeg_offset_ut_str,
                            eeg_end_ut_str))
                    summary.append(
                        'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s"\'s seizure offset time %s is later than EEG or wristband end time %s' % (
                            SZR_LATE_OFFSET, patient_id, event_name, redcap_repeat_instance, eeg_offset_ut_str,
                            eeg_end_ut_str))

                eeg_onset_uts.append(eeg_onset_ut)
                eeg_offset_uts.append(eeg_offset_ut)

                if not summary:
                    summary.append('Seizure on/offset time are within EEG start/end time scope')
                upload_eeg_log(project, patient_id, unique_event_name, redcap_repeat_instrument, redcap_repeat_instance,
                               summary)

        # for each events check if there is any overlap
        idx = np.argsort(eeg_onset_uts)
        eeg_onset_uts.sort()
        for ii in range((len(eeg_onset_uts) - 1)):
            # eeg_onset_ut = eeg_onset_uts[ii]
            eeg_offset_ut = eeg_offset_uts[idx[ii]]
            if eeg_offset_ut > eeg_onset_uts[ii + 1]:
                eeg_onset_ut_str = get_datetime(eeg_onset_uts[ii])
                eeg_offset_ut_str = get_datetime(eeg_offset_ut)
                eeg_onset_ut_str_next = get_datetime(eeg_onset_uts[ii + 1])
                eeg_offset_ut_str_next = get_datetime(eeg_offset_uts[idx[ii + 1]])
                # print(
                #     'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%d"\'s: (%s ~ %s) overlapped with instance %d: (%s ~ %s)'
                #     % (SZR_OVERLAP, patient_id, event_name, idx[ii] + 1, eeg_onset_ut_str, eeg_offset_ut_str,
                #        idx[ii + 1] + 1, eeg_onset_ut_str_next, eeg_offset_ut_str_next))
                print(
                    'WarnCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%d"\'s: (%s ~ %s) overlapped with instance %d: (%s ~ %s)'
                    % (SZR_OVERLAP, patient_id, event_name, redcap_repeat_instances[idx[ii] ], eeg_onset_ut_str, eeg_offset_ut_str,
                       redcap_repeat_instances[idx[ii + 1]], eeg_onset_ut_str_next, eeg_offset_ut_str_next))


def chk_eeg_anno(project, patient_id):
    patient_id_list = get_unique_patient_id_for_ibm(project, export_flag_field, ibm_flag_idx)
    print('Patient ID List = %s' % patient_id_list)

    if patient_id:
        if patient_id.upper() in patient_id_list:
            print('\nChecking patient_id=%s\'s EEG annotation Data ...' % patient_id)
            chk_eeg_anno_1_patient(project, patient_id)
        else:
            print('Err! patient_id=%s doesn\'t exist in the database' % patient_id)
    else:
        for idx, patient_id in enumerate(patient_id_list):
            print('\n%d/%d: Checking patient_id=%s\'s EEG annotation Data ...' % (
            idx + 1, len(patient_id_list), patient_id))
            chk_eeg_anno_1_patient(project, patient_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check Seizure Annotation Data Quality')

    parser.add_argument('--api_url', type=str, default='https://redcap.tch.harvard.edu/redcap_edc/api/',
                        help='Redcap API\'s url')

    parser.add_argument('--api_key', type=str, default='',
                        help='Redcap API\'s key')
    parser.add_argument('--patient_id', type=str,
                        help='format: Cxxx. If not specified, check all patients')

    args = parser.parse_args()

    try:
        project = Project(args.api_url, args.api_key)
    except:
        print('Fail to connect RedCap, please make sure you have correct--api_url and --api_key')
        exit()

    # args.patient_id = 'C479'
    # args.patient_id = 'TS TEST'
    # args.patient_id = 'C242'

    chk_eeg_anno(project, args.patient_id)
    print('\nCheck EEG Annotation is done')
