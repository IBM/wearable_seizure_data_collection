import os
import sys

print('Current working path is %s' % str(os.getcwd()))
sys.path.insert(0, os.getcwd())

import argparse
from redcap import Project
from data_collection.redcap_lib import *
from data_collection.constants import *
from datetime import datetime
from utils.common_func import get_unix_time
from utils.common_func import get_immediate_subdirectories
from utils.common_func import get_datetime
from data_collection.read_wrist_id import *
import math

import pickle

from data_annotation.get_parameters import get_parameters
from data_annotation.anno_lib import *

paras = get_parameters()

root_dir = paras.root_dir
out_dir = paras.out_dir
offline_clock_err = paras.offline_clock_err
extension_start = paras.extension_start
extension_end = paras.extension_end

patient_id_list = get_unique_patient_id_for_ibm(paras.project, export_flag_field, ibm_flag_idx)
print('In total %d Patients in REDCap= %s' % (len(patient_id_list),patient_id_list))

# #GTC Patient
patient_files = get_immediate_files(os.path.join(out_dir,'raw_data'))
patient_id_list = [x[:-4] for x in sorted(patient_files)]
print('In total %d Patients with data = %s' % (len(patient_id_list),patient_id_list))

patient_id = paras.patient_id
if patient_id:
    if patient_id.upper() in patient_id_list:
        patient_id_list=[patient_id]

# patient_id_list = ['C507']

valid_szr_count = 0
skipped_szr_count = 0
non_szr_count = 0

not_found_szr_num = 0
found_szr_num = 0
szr_total_dur = 0

wrst_labeled_dur = 0   # include sessions with and without seizures
wrst_labeled_with_szr_dur = 0  # only include sessions with seizures
wrst_total_dur = 0

# go through all the patients
for idx, patient_id in enumerate(sorted(patient_id_list)):
    print('\n%d/%d: processing patient_id=%s \'s wristband Data Annotation...' % (
        idx + 1, len(patient_id_list), patient_id))

    # initial wristband data label
    wrst_data_label_dicts = init_label_pkl(paras,patient_id)

    # get_wrst_placement information
    wrst_placements = get_wrst_placement(paras.project, patient_id, paras)

    # get szr information
    szrs= get_szrs(paras.project, patient_id, paras)

    # decide if whole wristband placement will be skipped due to cluster szrs or no eeg seizures
    # wrst_placements = update_wrst_placement(wrst_placements,szrs)

    # load corresponding patient raw data
    wrst_file_name = os.path.join(paras.wrst_raw_data_dir, patient_id + '.pkl')
    wrst_data_dicts = load_wrst_data(wrst_file_name)

    # annotation
    for wrst_placement in wrst_placements:

        # if wrst_placement['skip'] == True:
        #    continue

        wrst_start_ut = wrst_placement['wrst_start_ut']
        wrst_end_ut = wrst_placement['wrst_end_ut']
        eeg_start_btn_press_ut = wrst_placement['eeg_start_btn_press_ut']
        eeg_end_btn_press_ut = wrst_placement['eeg_end_btn_press_ut']
        wrst_loc = wrst_placement['wrst_loc']
        err_per_sec = wrst_placement['err_per_sec']
        timing_err = wrst_placement['start_timing_err']
        timing_case = wrst_placement['timing_case']
        enroll_age = wrst_placement['enroll_age']
        enroll_sex = wrst_placement['enroll_sex']

        # by default labelled
        wrst_placement['labelled'] = True
        wrst_placement['issues'] = 'none'

        # go through all szrs, if found overlapped szr had no eeg, skip the whole placement
        for szr in szrs:
            eeg_szr_onset_ut = szr['eeg_szr_onset_ut']
            eeg_szr_offset_ut = szr['eeg_szr_offset_ut']
            eeg_szr_onset_t = szr['eeg_szr_onset_t']
            eeg_szr_offset_t = szr['eeg_szr_offset_t']
            szr_duration = eeg_szr_offset_ut-eeg_szr_onset_ut

            # for szr overlapped with wrst_start_ut and wrst_end_ut
            if (wrst_start_ut <= eeg_szr_offset_ut) and (wrst_end_ut >= eeg_szr_onset_ut):

                if szr['correct_onoffset_flag'] == False: # no correct on offset
                    wrst_placement['labelled'] = False
                    wrst_placement['issues'] = szr['szr_semiology'][0] + ' no correct onset or offset'
                    print(
                        'Event: %s, wrst_placement instance: %d is not labelled due to seizure: %s no correct onset or offset' % (
                            wrst_placement['event_name'], wrst_placement[
                                'redcap_repeat_instance'], szr['szr_semiology'][0]))
                    break

                # if szr['szr_semiology'][1] == 'no eeg':
                #     wrst_placement['labelled'] = False
                #     wrst_placement['issues'] = szr['szr_semiology'][0] + ' no eeg'
                #     print('Event: %s, wrst_placement instance: %d not labelled due to seizure: %s no eeg' % (
                #     wrst_placement['event_name'], wrst_placement[
                #         'redcap_repeat_instance'], szr['szr_semiology'][0]))
                #     break

        # go through all wristband signal,
        # if wristband data is overlapped with wrist placement, then mark it labelled initially
        for wrst_data_dict in wrst_data_dicts:
            location = str(wrst_data_dict['location'])
            if location.startswith(wrst_loc):
                wrst_session_start_ut = wrst_data_dict['start_unix_t']
                wrst_session_end_ut = wrst_data_dict['end_unix_t']

                # if wristband data is overlapped with wrist placement, then mark it labelled
                if (wrst_end_ut >= wrst_session_start_ut) and (
                        wrst_start_ut <= wrst_session_end_ut):
                    wrst_data_index = wrst_data_dict['wrst_data_index']
                    wrst_data_label_dict = wrst_data_label_dicts[wrst_data_index]
                    wrst_data_label_dict['redcap_repeat_instance'] = wrst_placement['redcap_repeat_instance']
                    wrst_data_label_dict['unique_event_name'] = wrst_placement['unique_event_name']
                    wrst_data_label_dict['labelled'] = wrst_placement['labelled']
                    wrst_data_label_dict['issues'] = wrst_placement['issues']
                    wrst_data_label_dict['enroll_sex'] = enroll_sex
                    wrst_data_label_dict['enroll_age'] = enroll_age

        if wrst_placement['labelled'] == False:
            continue

        # go through all the szrs, find their correspoding data,
        # for clustered szr, skip the whole session by setting the 'labelled' to be fause
        for szr in szrs:
            eeg_szr_onset_ut = szr['eeg_szr_onset_ut']
            eeg_szr_offset_ut = szr['eeg_szr_offset_ut']
            eeg_szr_onset_t = szr['eeg_szr_onset_t']
            eeg_szr_offset_t = szr['eeg_szr_offset_t']
            szr_duration = eeg_szr_offset_ut-eeg_szr_onset_ut

            # for szr overlapped with wrst_start_ut and wrst_end_ut
            if (wrst_start_ut <= eeg_szr_offset_ut) and (wrst_end_ut >= eeg_szr_onset_ut):

                if eeg_start_btn_press_ut != -1:
                    cmpnst_szr_onset_ut = eeg_szr_onset_ut - err_per_sec * (
                            eeg_szr_onset_ut - eeg_start_btn_press_ut)
                    cmpnst_szr_offset_ut = eeg_szr_offset_ut - err_per_sec * (
                            eeg_szr_offset_ut - eeg_start_btn_press_ut)
                else:
                    # use wrst start t to replace roughly
                    cmpnst_szr_onset_ut = eeg_szr_onset_ut - err_per_sec * (
                            eeg_szr_onset_ut - wrst_start_ut)
                    cmpnst_szr_offset_ut = eeg_szr_offset_ut - err_per_sec * (
                            eeg_szr_offset_ut - wrst_start_ut)

                # try to find szr's corresponding wristband data
                found = False
                for wrst_data_dict in wrst_data_dicts:
                    location = str(wrst_data_dict['location'])
                    if location.startswith(wrst_loc):
                        wrst_session_start_ut = wrst_data_dict['start_unix_t']
                        wrst_session_end_ut = wrst_data_dict['end_unix_t']
                        if (cmpnst_szr_offset_ut >= wrst_session_start_ut) and (
                                cmpnst_szr_onset_ut <= wrst_session_end_ut):
                            found = True
                            break

                if not found:
                    print(
                        'ErrorCode%d! Patient %s, Seizure %s can\'t find Seizure from %s to %s\'s in %s'
                        % (WRST_SESSION_NOT_FOUND, patient_id, szr['szr_semiology'][0], eeg_szr_onset_t, eeg_szr_offset_t, wrst_loc))
                    not_found_szr_num += 1

                else:
                    # if found, then locate its data label dictionary
                    wrst_data_index = wrst_data_dict['wrst_data_index']
                    wrst_data_label_dict = wrst_data_label_dicts[wrst_data_index]

                    szr_used_ibm_flag = szr['szr_used_ibm_flag']
                    szr_cluster = szr['szr_cluster']

                    # if szr['szr_semiology'][1] == 'no eeg':
                    #     wrst_data_label_dict['labelled'] = False
                    #     wrst_data_label_dict['issues'] = 'no eeg'
                    #     print('Event: %s, wrst_placement instance: %d seizure: %s is not labelled due to no eeg' % (wrst_placement['event_name'], wrst_data_label_dict[
                    #         'redcap_repeat_instance'],szr['szr_semiology'][0] ))
                    #     continue

                    # check if is szr cluster, 0: all good. 1,2,3 cluster or other problem
                    '''
                    seizure_cluster	"Is this a group of seizures with one timestamp? 
                    1, Yes 
                    2, No, this is an individual seizure, and PART OF A CLUSTER. 
                    0, No, this is an isolated seizure, NOT part of a cluster. 
                    3, Not Applicable-Because EEG Not Available, Not a Seizure, Not on Recording
                    '''
                    if paras.inc_szr_cluster == 0:
                        if szr_cluster != '0':
                            wrst_data_label_dict['labelled'] = False
                            wrst_data_label_dict['issues'] = szr_cluster_list[int(szr_cluster)]
                            print(
                                'Event: %s, wrst_placement instance: %d seizure: %s is not labelled due to %s' % (
                                wrst_placement['event_name'], wrst_data_label_dict[
                                    'redcap_repeat_instance'], szr['szr_semiology'][0], szr_cluster_list[int(szr_cluster)]))
                            continue

                    # should be useless now...
                    if szr_cluster == '0' and szr['correct_onoffset_flag']==False: # no correct on offset for a normal seizure
                        wrst_data_label_dict['labelled'] = False
                        wrst_data_label_dict['issues'] = 'no correct on offset for a normal seizure'
                        print(
                            'Event: %s, wrst_placement instance: %d seizure: %s is not labelled due to no correct on offset for a normal seizure' % (
                                wrst_placement['event_name'], wrst_data_label_dict[
                                    'redcap_repeat_instance'], szr['szr_semiology'][0]))
                        continue

                    if szr['szr_semiology'][1] == 'szr free':
                        print('szr free')
                        continue

                    # if szr['szr_semiology'][1] == 'no data':
                    #     print('no data')
                    #     continue


                    ####################################################################
                    # according to email in 20210208, this field won't be used any more
                    ####################################################################
                    # # check if "sz_used_ibm" 1: use 0,2 not used
                    # # 1, Sent to IBM & Used | 2, Sent to IBM & Not Used | 3, Not Sent to IBM
                    # if szr_used_ibm_flag != '1':
                    #     wrst_data_label_dict['labelled'] = False
                    #     if szr_used_ibm_flag == '3':
                    #         wrst_data_label_dict['issues'] = 'Not Sent to IBM'
                    #         print('Event: %s, wrst_placement instance: %d not labelled due to seizure: %s %s' % (wrst_placement['event_name'], wrst_data_label_dict[
                    #             'redcap_repeat_instance'],szr['szr_semiology'][0],wrst_data_label_dict['issues']))
                    #     elif szr_used_ibm_flag == '2':
                    #         wrst_data_label_dict['issues'] = 'Sent to IBM & Not Used'
                    #         print(
                    #             'Event: %s, wrst_placement instance: %d not labelled due to seizure: %s %s' % (
                    #             wrst_placement['event_name'], wrst_data_label_dict[
                    #                 'redcap_repeat_instance'], szr['szr_semiology'][0],wrst_data_label_dict['issues']))
                    #     continue

                    wrst_szr_onset_shift = math.floor(
                        cmpnst_szr_onset_ut - wrst_session_start_ut + timing_err)
                    wrst_szr_offset_shift = math.ceil(
                        cmpnst_szr_offset_ut - wrst_session_start_ut + timing_err)

                    # Subtract extension_start to wrst_szr_onset_shift, min value is 0 add extension_end to wrst_szr_offset_shift, max value is total sample time
                    dur = wrst_session_end_ut - wrst_session_start_ut

                    if szr['szr_semiology'][1] == 'szr':
                        wrst_szr_onset_shift = max(0, wrst_szr_onset_shift - extension_start)
                        wrst_szr_offset_shift = min(dur, wrst_szr_offset_shift + extension_end)

                    else:
                        wrst_szr_onset_shift = max(0, wrst_szr_onset_shift - extension_start - paras.szr_cluster_win)
                        wrst_szr_offset_shift = min(dur, wrst_szr_offset_shift + extension_end + paras.szr_cluster_win)
                        print('Event: %s, wrst_placement instance: %d seizure: %s labelled but not used: %s because %s' % (
                            wrst_placement['event_name'], wrst_data_label_dict['redcap_repeat_instance'],
                            szr['szr_semiology'][0],szr_cluster_list[int(szr_cluster)],szr['szr_semiology'][1] ))

                    # start labelling
                    wrst_data_label_dict['seizures'].append((wrst_szr_onset_shift, wrst_szr_offset_shift))
                    wrst_data_label_dict['seizure_num'] += 1
                    wrst_data_label_dict['szr_cluster'].append(szr['szr_semiology'][1])

                    # From seizure start to end, label as 1
                    wrst_data_label_dict['label'][wrst_szr_onset_shift:wrst_szr_offset_shift] = 1

                    # how to add seizure semiology?
                    wrst_data_label_dict['szr_semiology'][wrst_szr_onset_shift:wrst_szr_offset_shift] = szr['szr_semiology']

                    found_szr_num += 1
                    szr_total_dur += szr_duration

                    # update the seizure usage
                    # if paras.inc_szr_cluster == 1:
                    #     # szr_wrst_loc	0, Not used | 1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown
                    #     upload_szr_wrst_loc(paras.project, patient_id,
                    #                         szr['unique_event_name'],
                    #                         szr['redcap_repeat_instrument'],
                    #                         szr['redcap_repeat_instance'],
                    #                        wrst_loc, 1)
                    if szr['szr_semiology'][1] == 'szr':
                        # szr_wrst_loc	0, Not used | 1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown
                        upload_szr_wrst_loc(paras.project, patient_id,
                                            szr['unique_event_name'],
                                            szr['redcap_repeat_instrument'],
                                            szr['redcap_repeat_instance'],
                                            wrst_loc, 1)


        # stats
        wrst_dur = wrst_end_ut-wrst_start_ut
        if wrst_placement['labelled']:
            wrst_labeled_dur += wrst_dur # include sessions with and without seizures
            if found_szr_num>=1:
                wrst_labeled_with_szr_dur += wrst_dur # only include sessions with seizures

        wrst_total_dur += wrst_dur  # include all the wristband sessions


    # update labelling file
    if 1:
        wrst_data_label_file_name = os.path.join(paras.wrst_data_label_dir, patient_id + '.pkl')
        pickling_on = open(wrst_data_label_file_name, "wb")
        pickle.dump(wrst_data_label_dicts, pickling_on)
        pickling_on.close()

        update_szr_usage(paras.project, patient_id, wrst_placements, szrs, wrst_data_dicts, wrst_data_label_dicts)


# print output
print('valid_szr_count = ', valid_szr_count)
print('skipped_szr_count = ', skipped_szr_count)
print('non_szr_count = ', non_szr_count)
print('not_found_szr_num = ', not_found_szr_num)
print('found_szr_num = ', found_szr_num)
print('szr_total_dur = ', szr_total_dur)

print('wrst_labeled_with_szr_dur = ', wrst_labeled_with_szr_dur)
print('wrst_labeled_dur = ', wrst_labeled_dur)
print('wrst_total_dur = ', wrst_total_dur)

