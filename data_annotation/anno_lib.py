import pickle
# import os
import numpy as np
# import argparse
# from redcap import Project
from data_collection.redcap_lib import *
from data_collection.constants import *
from datetime import datetime
from utils.common_func import get_unix_time
from utils.common_func import get_immediate_subdirectories
from utils.common_func import get_datetime
from data_collection.read_wrist_id import *
from collections import namedtuple

# Szr_semiology = namedtuple('Szr_semiology',
#                                ['szr_label', 'base_type', 'motor_type', 'sub_type', 'focal_aware_type'])

# ('szr_id','S8') 'Cxxx_sss_nnn' sss: fir(st),sec(ond),third,fourth,fifth,sixth,seventh,eighth,ninth,tenth,ele,twe
Szr_semiology = np.dtype([('szr_id','S12'),('szr_label','S8'),('base_type','S9'),('motor_type','S11'),('sub_type','S16'),('focal_aware_type','S8')])
#Szr_semiology = np.dtype([('szr_label','S8'),('base_type','S9'),('motor_type','S11'),('sub_type','S16'),('focal_aware_type','S8')])
#Szr_semiology = np.dtype([('szr_label','S20'),('base_type','S20'),('motor_type','S20'),('focal_aware_type','S20'),('sub_type','S20')])

# init wristband label according to wristband data
def init_label_pkl(paras, patient_id):
    wrst_file_name = os.path.join(paras.wrst_raw_data_dir, patient_id + '.pkl')
    pickling_on = open(wrst_file_name, "rb")
    wrst_data_dicts = pickle.load(pickling_on)
    pickling_on.close()

    wrst_data_label_dicts = []
    for wrst_data_dict in wrst_data_dicts:
        wrst_data_label_dict = {'wrst_data_index': wrst_data_dict['wrst_data_index']}
        wrst_data_label_dict['labelled'] = False
        wrst_data_label_dict['issues'] = 'none'  # by default is normal
        wrst_data_label_dict['start_t'] = wrst_data_dict['start_t']
        wrst_data_label_dict['end_t'] = wrst_data_dict['end_t']
        wrst_data_label_dict['start_unix_t'] = wrst_data_dict['duration']
        wrst_data_label_dict['start_unix_t'] = wrst_data_dict['start_unix_t']
        wrst_data_label_dict['end_unix_t'] = wrst_data_dict['end_unix_t']
        wrst_data_label_dict['date'] = wrst_data_dict['date']
        wrst_data_label_dict['location'] = wrst_data_dict['location']

        duration = wrst_data_dict['duration']
        wrst_data_label_dict['label'] = np.zeros([duration, 1])
        wrst_data_label_dict['szr_semiology'] = np.empty(duration, dtype=Szr_semiology)
        wrst_data_label_dict['szr_semiology'][:] = ('','szr free','invalid','invalid','invalid','invalid')
        wrst_data_label_dict['seizure_num'] = 0
        wrst_data_label_dict['seizures'] = []
        wrst_data_label_dict['szr_cluster'] = []

        wrst_data_label_dicts.append(wrst_data_label_dict)
    wrst_data_label_file_name = os.path.join(paras.wrst_data_label_dir, patient_id + '.pkl')
    if os.path.exists(wrst_data_label_file_name):
        os.remove(wrst_data_label_file_name)
    pickling_on = open(wrst_data_label_file_name, "wb")
    pickle.dump(wrst_data_label_dicts, pickling_on)
    pickling_on.close()

    return wrst_data_label_dicts



def get_wrst_placement(project, patient_id, args):

    wrst_data_root_dir = args.root_dir
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

    # first_enroll_age = patient_data_all[0][first_enroll_age_field]
    # first_enroll_date = patient_data_all[0][first_enroll_date_field]

    # initialise wristband placement data dictionary
    wrst_placements = []

    # read wrist band id configuration
    wrst_id_dict = read_wrist_id('data_collection/wristband_id.txt')

    # extract each event's data. Event  it is best to process data event by event, to improve in the future!
    for event in events:
        patient_data_list = get_events_data(patient_data_all, event)

        if not patient_data_list:  # no test data found
            continue

        unique_event_name = event['unique_event_name']
        event_name = event['event_name']

        #enroll_idx = 0

        for patient_data in patient_data_list:

            summary = []

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']

            #
            if redcap_repeat_instrument == '' and redcap_repeat_instance == '':
                #enroll_idx +=1
                enroll_age =  patient_data[enroll_age_field]
                enroll_sex = patient_data[gender_field]
                exclude_enroll_flag = patient_data[exclude_enroll_flag_field]
                if exclude_enroll_flag:
                    if int(exclude_enroll_flag)==1: # whole enrollment data skipped
                        continue
                else:
                    print(
                        'ErrCode%d! Patient: "%s" Event: "%s" didn\'t indicate excluded or not' % (
                            WRST_NO_LOCATION, patient_id, event_name))

            if redcap_repeat_instrument == wrst_place_instru:

                wrst_loc_idx = patient_data[wrst_location_field]
                # didn't indicate the wristband location
                if not wrst_loc_idx:
                    print(
                        'ErrCode%d! Patient: "%s" Event: "%s" Wristband Instance: "%s" didn\'t indicate wristband location' % (
                            WRST_NO_LOCATION, patient_id, event_name, redcap_repeat_instance))
                    continue

                wrst_loc = wrst_loc_list[int(wrst_loc_idx) - 1].lower()

                # signal downloaded or not
                sig_downloaded = int(patient_data[wrst_download_flag_field])
                if sig_downloaded == 0:
                    print('Event: "%s" wrst_placement Instance: "%s" signal not downloaded for "%s"'% (
                            event_name, redcap_repeat_instance, wrst_loc))
                    continue

                # used or not, decided by code
                wrst_usage_flag = patient_data[wrst_usage_field]
                if wrst_usage_flag=='0' : # whole wristband placement are not used

                    # Reasons for not using the wristband data
                    #     No raw data
                    #     Raw data too short
                    #     Missing EEG onset/offset definition
                    #     Not used for other reasons
                    wrst_not_use_reasons = patient_data[wrst_not_use_reasons_field]
                    wrst_not_use_reason = wrst_not_use_reason_list[int(wrst_not_use_reasons)]
                    print('Event: %s, wrst_placement instance: %d are skipped due to %s' % (
                    event_name, redcap_repeat_instance,wrst_not_use_reason))
                    continue

                # used or not, decided by BCH
                sig_usage_flag = patient_data[sig_usage_flag_field]
                if wrst_usage_flag=='0' : # whole wristband placement are not used
                    print('Event: %s, wrst_placement instance: %d are skipped due to BCH' % (
                        event_name, redcap_repeat_instance))
                    continue

                timing_case = patient_data[wrst_case_field]
                timing_case = int(timing_case)
                start_timing_err = float(patient_data[start_timing_err_field])
                end_timing_err = float(patient_data[end_timing_err_field])
                err_per_sec =  float(patient_data[err_per_sec_field])

                if timing_case==1: # ideal case
                    start_timing_err = 0.0
                    err_per_sec = 0.0
                elif timing_case==2: # with start timing
                    err_per_sec = args.offline_clock_err / 86400

                summary, eeg_start_btn_press_ut, eeg_end_btn_press_ut = get_eeg_start_end_btn_press_ut(patient_data, patient_id, event_name,
                                                                                                       redcap_repeat_instance, summary)

                # get wristband start/off time
                wrst_start_t = patient_data[wrst_start_t_field]
                wrst_end_t = patient_data[wrst_end_t_field]
                wrst_start_ut = get_unix_time(wrst_start_t,"%Y-%m-%d %H:%M:%S")
                wrst_end_ut = get_unix_time(wrst_end_t,"%Y-%m-%d %H:%M:%S")

                wrst_placement = {}

                wrst_placement['unique_event_name'] = unique_event_name
                wrst_placement['event_name'] = event_name
                wrst_placement['redcap_repeat_instance']=redcap_repeat_instance


                wrst_placement['wrst_start_t']=wrst_start_t
                wrst_placement['wrst_end_t'] = wrst_end_t
                wrst_placement['wrst_start_ut'] = wrst_start_ut
                wrst_placement['wrst_end_ut'] = wrst_end_ut

                wrst_placement['eeg_start_btn_press_ut'] = eeg_start_btn_press_ut
                wrst_placement['eeg_start_t'] = get_datetime(eeg_start_btn_press_ut,"%Y-%m-%d %H:%M:%S")
                wrst_placement['eeg_end_btn_press_ut'] = eeg_end_btn_press_ut
                wrst_placement['eeg_end_btn_press_t'] = get_datetime(eeg_end_btn_press_ut,"%Y-%m-%d %H:%M:%S")

                wrst_placement['err_per_sec'] = err_per_sec
                wrst_placement['start_timing_err'] = start_timing_err
                wrst_placement['timing_case'] = timing_case
                wrst_placement['enroll_age'] = enroll_age
                wrst_placement['enroll_sex'] = enroll_sex
                wrst_placement['wrst_loc'] = wrst_loc
                wrst_placement['skip'] = False # default we will include all the data
                wrst_placement['timing_case'] = timing_case

                wrst_placements.append(wrst_placement)

    return wrst_placements

# decide if whole wristband placement will be skipped due to cluster szrs or no eeg seizures
def update_wrst_placement(wrst_placements, szrs):

    for wrst_sess_id, wrst_placement in enumerate(wrst_placements):

        print('Processing wristband session ', wrst_sess_id)

        wrst_start_ut = wrst_placement['wrst_start_ut']
        wrst_end_ut = wrst_placement['wrst_end_ut']

        for szr in szrs:
            eeg_szr_onset_ut = szr['eeg_szr_onset_ut']
            eeg_szr_offset_ut = szr['eeg_szr_offset_ut']

            # for szr overlapped with wrst_start_ut and wrst_end_ut
            if (wrst_start_ut <= eeg_szr_offset_ut) and (wrst_end_ut >= eeg_szr_onset_ut):

                if szr['szr_cluster'] != '0':
                    wrst_placement['skip'] = True
                    print('wrst_placement instance %d not labelled due to seizure cluster'%wrst_placement['redcap_repeat_instance'])
                    break

                if szr['szr_semiology'][0] == 'no eeg':
                    wrst_placement['skip'] = True
                    print('wrst_placement instance %d not labelled due to no eeg'%wrst_placement['redcap_repeat_instance'])
                    break

    return wrst_placements


def load_wrst_data(wrst_file_name):
    pickling_on = open(wrst_file_name, "rb")
    wrst_data_dicts = pickle.load(pickling_on)
    pickling_on.close()
    return wrst_data_dicts

def get_szr_semiology(patient_data, patient_id, event_name, redcap_repeat_instance):

    # 'szr_id', 'szr_label', 'base_type', 'motor_type', 'focal_aware_type', 'sub_type'

    szr_id = str(patient_id)+'_'+event_name[0:3]+'_'+'{0:03d}'.format(redcap_repeat_instance)
    szr_cluster  = patient_data[szr_cluster_field]

    '''
    1, Focal onset
    2, Generalized onset
    4, Unknown onset/Unclassified onset
    a szr without proof from EEG, will discard the corresponding wristband session -> 5, EEG Not Available-EEG Not Available
    treat as background -> 6, Not A Seizure/ Or Is a seizure and not on wristband recording
    '''
    szr_base_type = patient_data[sz_type_enroll_new_field]


    szr_subclinic_flag = patient_data[subclinic_sz_field]
    '''
    available for 1,2,4, YES/No
    '''
    szr_motor_type = patient_data[onset_mov_field]
    '''
    1, Motor
    2, Non-motor
    3, Not Available/Patient off Camera-EEG Video
    4, Unclassified-Unable to clinically classify
    '''
    szr_focal_aware_type = patient_data[focal_aware_field]
    '''
    1, Aware
    2, Impaired awareness
    3, Unclassified-Clinically you can't classify
    4, Not Applicable for: Focal To Bilateral Tonic-Clonic
    '''

    szr_focal_motor_sub_type = patient_data[focal_motor_field]

    '''
    1, Automatisms
    2, Atonic
    3, Clonic
    4, Epileptic spasms
    5, Hyperkinetic
    6, Myoclonic
    7, Tonic
    8, Bilateral tonic-clonic
    9, Unclassified-Unable to clinically classify
    '''

    szr_focal_non_motor_sub_type = patient_data[focal_non_mo_field]

    '''
    1, Autonomic
    2, Behavior arrest
    3, Cognitive
    4, Emotional
    5, Sensory
    6, Unclassified-Unable to clinically classify
    '''

    szr_gnr_motor_sub_type = patient_data[generalized_motor_field]

    '''
    1, Tonic-clonic
    2, Clonic
    3, Tonic
    4, Myoclonic
    5, Myoclonic-tonic-clonic
    6, Myoclonic-atonic
    7, Atonic
    8, Epileptic spasms
    9, Unclassified-Unable to clinically classify
    '''
    szr_gnr_non_motor_sub_type = patient_data[generalized_non_motor_field]

    '''
    1, Tonic-clonic
    2, Epileptic spasms
    3, Unclassified-Unable to clinically classify
    '''
    szr_unk_motor_sub_type = patient_data[unknown_motor_manif_field]

    '''
    1, Tonic-clonic
    2, Epileptic spasms
    3, Unclassified-Unable to clinically classify
    '''
    szr_unk_non_motor_sub_type = patient_data[un_nonmotor_manif_field]

    '''
    1, Yes
    0, No 
    '''

    '''
    szr_label: szr (1), control (0), invalid (-1)
    base_type: focal(0), generalised(1), unknown(2)
    motor_type: motor, non_motor, unclassified, subclinical
    focal_aware_type: aware, impaired_aware, unclassified, btc
    sub_type: varies according base_type and motor_type
    '''

    '''
    sz_type_enroll_new	
    1, Focal onset | 2, Generalized onset | 4, Unknown/Unclassified onset 
    | 5, EEG Not Available-EEG Not Available because you need the EEG to answer this question and all the other questions below. No other questions should open up. GAME OVER. 
    | 6, Not A Seizure  | 7, Seizure not on wristband											
    '''

    if szr_base_type == '1': # focal
        if szr_cluster == '0':
            szr_label = 'szr'
        elif szr_cluster == '1':
            szr_label = 'szr clst'
        elif szr_cluster == '2':
            szr_label = 'szr part'
        elif szr_cluster == '3':
            szr_label = 'not appl' # not applicable

        base_type = szr_base_type_list[int(szr_base_type)-1]

        if szr_subclinic_flag == '1':
            motor_type = 'subclinical'
            sub_type = 'invalid'
            focal_aware_type = 'invalid'
        else:
            motor_type = szr_motor_type_list[int(szr_motor_type)-1]
            if szr_motor_type =='1': # motor
                sub_type = szr_focal_motor_sub_type_list[int(szr_focal_motor_sub_type) - 1]
                focal_aware_type = szr_focal_aware_type_list[int(szr_focal_aware_type) - 1]
            elif szr_motor_type =='2': # non motor
                sub_type = szr_focal_non_motor_sub_type_list[int(szr_focal_non_motor_sub_type)-1]
                focal_aware_type = szr_focal_aware_type_list[int(szr_focal_aware_type) - 1]
            else:
                sub_type = 'invalid'
                focal_aware_type = 'invalid'

    elif szr_base_type == '2':
        if szr_cluster == '0':
            szr_label = 'szr'
        elif szr_cluster == '1':
            szr_label = 'szr clst'
        elif szr_cluster == '2':
            szr_label = 'szr part'
        elif szr_cluster == '3':
            szr_label = 'not appl'  # not applicable

        base_type = szr_base_type_list[int(szr_base_type)-1]
        focal_aware_type = 'invalid'
        if szr_subclinic_flag == '1':
            motor_type = 'subclinical'
            sub_type = 'invalid'
        else:
            motor_type = szr_motor_type_list[int(szr_motor_type) - 1]
            if szr_motor_type == '1':  # motor
                sub_type = szr_gnr_motor_sub_type_list[int(szr_gnr_motor_sub_type) - 1]
            elif szr_motor_type == '2':  # non motor
                sub_type = szr_gnr_non_motor_sub_type_list[int(szr_gnr_non_motor_sub_type) - 1]
            else:
                sub_type = 'invalid'

    elif szr_base_type == '4':
        if szr_cluster == '0':
            szr_label = 'szr'
        elif szr_cluster == '1':
            szr_label = 'szr clst'
        elif szr_cluster == '2':
            szr_label = 'szr part'
        elif szr_cluster == '3':
            szr_label = 'not appl'  # not applicable

        base_type = szr_base_type_list[int(szr_base_type)-1]
        focal_aware_type = 'invalid'
        if szr_subclinic_flag == '1':
            motor_type = 'subclinical'
            sub_type = 'invalid'
            focal_aware_type = 'invalid'
        else:
            motor_type = szr_motor_type_list[int(szr_motor_type) - 1]
            if szr_motor_type == '1':  # motor
                sub_type = szr_unk_motor_sub_type_list[int(szr_unk_motor_sub_type) - 1]
            elif szr_motor_type == '2':  # non motor
                sub_type = szr_unk_non_motor_sub_type_list[int(szr_unk_non_motor_sub_type) - 1]
            else:
                sub_type = 'invalid'

    elif szr_base_type == '5':#| 5, EEG Not Available
        szr_label = 'no eeg'
        base_type = 'invalid'
        motor_type = 'invalid'
        focal_aware_type = 'invalid'
        sub_type = 'invalid'
    elif szr_base_type == '6': #| 6, Not A Seizure
        szr_label = 'szr free'
        base_type = 'invalid'
        motor_type = 'invalid'
        focal_aware_type = 'invalid'
        sub_type = 'invalid'
    elif szr_base_type == '7': # | 7, Seizure not on wristband
        szr_label = 'no data'
        base_type = 'invalid'
        motor_type = 'invalid'
        focal_aware_type = 'invalid'
        sub_type = 'invalid'
    else:
        print('wrong seizure type')

    # szr_semiology = Szr_semiology(szr_label=szr_label, base_type=base_type, motor_type=motor_type,
    #                               sub_type=sub_type, focal_aware_type=focal_aware_type)

    szr_semiology = (szr_id, szr_label, base_type, motor_type, sub_type, focal_aware_type)

    return szr_semiology

def get_eeg_szr_onset_offset_ut(patient_data, patient_id, event_name, redcap_repeat_instance):
    eeg_szr_onset_t_str = patient_data[eeg_szr_onset_field]
    eeg_szr_offset_t_str = patient_data[eeg_szr_offset_field]

    eeg_onset_date_str = patient_data['eeg_onset_date']
    eeg_offset_date_str = patient_data['eeg_offset_date']

    correct_onoffset_flag = True

    sz_type_enroll_new = int(patient_data[sz_type_enroll_new_field])-1
    szr_cluster = patient_data[szr_cluster_field]

    try:

        if eeg_szr_onset_t_str != '':
            eeg_szr_onset_ut = get_unix_time(eeg_szr_onset_t_str, "%Y-%m-%d %H:%M:%S")
        elif eeg_onset_date_str != '':
            print(
                'Patient: "%s" Event: "%s" Seizure Instance: "%s" has no seizure onset time but has onset date: %s, cluster: %s, seizure type is %s' % (
                    patient_id, event_name,
                    redcap_repeat_instance, eeg_onset_date_str,szr_cluster_list[int(szr_cluster)], sz_type_enroll_new_list[sz_type_enroll_new]))

            eeg_szr_onset_ut = get_unix_time(eeg_onset_date_str+ ' 23:59:59', "%Y-%m-%d %H:%M:%S")
            correct_onoffset_flag = False
        else:
            print(
                'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset: %s' % (
                    SZR_WRONG_DUR,
                    patient_id, event_name,
                    redcap_repeat_instance, eeg_szr_onset_t_str))

            eeg_szr_onset_ut = 0
            eeg_szr_offset_ut = 0
            correct_onoffset_flag = False
            return eeg_szr_onset_ut, eeg_szr_offset_ut, correct_onoffset_flag


        if eeg_szr_offset_t_str != '':
            eeg_szr_offset_ut = get_unix_time(eeg_szr_offset_t_str, "%Y-%m-%d %H:%M:%S")
            eeg_szr_dur = eeg_szr_offset_ut - eeg_szr_onset_ut

            # check if it is no EEG
            if  eeg_szr_offset_t_str=='1900-01-01 00:00:00':  # No EEG
                eeg_szr_offset_ut = eeg_szr_onset_ut
                eeg_szr_dur = eeg_szr_offset_ut - eeg_szr_onset_ut
                print(
                    'Patient: "%s" Event: "%s" Seizure Instance: "%s" has invalid seizure offset: 1900-01-01 00:00:00, cluster: %s, seizure type is %s' % (
                        patient_id, event_name,
                        redcap_repeat_instance,szr_cluster_list[int(szr_cluster)], sz_type_enroll_new_list[sz_type_enroll_new]))
                correct_onoffset_flag = False

        elif patient_data[dura_ltm_avai_field] == '1':
            eeg_szr_dur = float(patient_data[dura_ltm_field])
            eeg_szr_offset_ut = eeg_szr_dur + eeg_szr_onset_ut
        elif eeg_offset_date_str != '':
            print(
                'Patient: "%s" Event: "%s" Seizure Instance: "%s" has no seizure offset time but has offset date: %s, cluster: %s, seizure type is %s' % (
                    patient_id, event_name,
                    redcap_repeat_instance, eeg_offset_date_str,szr_cluster_list[int(szr_cluster)], sz_type_enroll_new_list[sz_type_enroll_new]))
            #eeg_szr_offset_ut = get_unix_time(eeg_offset_date_str + ' 23:59:59', "%Y-%m-%d %H:%M:%S")
            eeg_szr_offset_ut = eeg_szr_onset_ut
            eeg_szr_dur = eeg_szr_offset_ut - eeg_szr_onset_ut
            correct_onoffset_flag = False
        else:
            correct_onoffset_flag = False
            # # check if it is not applicable
            # if szr_cluster=='3': # not applicable
            #     eeg_szr_offset_ut = eeg_szr_onset_ut
            #     eeg_szr_dur = eeg_szr_offset_ut - eeg_szr_onset_ut
            #     print(
            #         'Patient: "%s" Event: "%s" Seizure Instance: "%s" has no seizure offset and it is not applicable' % (
            #             patient_id, event_name,
            #             redcap_repeat_instance, eeg_szr_offset_t_str))
            # else:
            print(
                'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure offset: %s or no duration, cluster: %s, seizure type is %s' % (
                    SZR_WRONG_DUR,
                    patient_id, event_name,
                    redcap_repeat_instance, eeg_szr_offset_t_str,szr_cluster_list[int(szr_cluster)], sz_type_enroll_new_list[sz_type_enroll_new]))

            eeg_szr_onset_ut =0
            eeg_szr_offset_ut =0
            return eeg_szr_onset_ut, eeg_szr_offset_ut, correct_onoffset_flag

        if eeg_szr_dur < 0:
            print(
                'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has negative duration, please check seizure onset/offset/duration time' % (
                    SZR_WRONG_DUR,
                    patient_id, event_name,
                    redcap_repeat_instance))

            eeg_szr_onset_ut = 0
            eeg_szr_offset_ut = 0
            correct_onoffset_flag = False
    except:
        print(
            'ErrCode%d! Patient: "%s" Event: "%s" Seizure Instance: "%s" has wrong seizure onset/offset/duration time' % (
                SZR_WRONG_DUR,
                patient_id, event_name,
                redcap_repeat_instance))

        eeg_szr_onset_ut = 0
        eeg_szr_offset_ut = 0

    return eeg_szr_onset_ut,eeg_szr_offset_ut, correct_onoffset_flag

def get_szrs(project, patient_id, paras):
    events = project.events

    ids_of_interest = ['redcap_event_name', patient_id]
    patient_data_all = project.export_records(records=ids_of_interest)
    if not patient_data_all:
        print('Error! No data was found. Please check your patient ID "%s"' % patient_id)
        return

    szrs = []
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


        # first, get all the onset/offset
        for patient_data in patient_data_list:

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']

            if redcap_repeat_instrument == szr_anno_instru:

                # todo: set szr to be not used by default
                # szr_wrst_loc	0, Not used | 1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown
                # szr_wrst_loc___0	szr_wrst_loc___1	szr_wrst_loc___2	szr_wrst_loc___3	szr_wrst_loc___4	szr_wrst_loc___5	szr_wrst_loc___6	szr_wrst_loc___7

                upload_szr_wrst_loc(project, patient_id, unique_event_name, redcap_repeat_instrument, redcap_repeat_instance,
                                        'not used',1)

                # IBM Seizure Used or Not Used?	1, Sent to IBM & Used | 2, Sent to IBM & Not Used | 3, Not Sent to IBM
                szr_used_ibm_flag = patient_data['sz_used_ibm']

                '''
                seizure_cluster	seizures_at_enrollment_repeat_events		radio	"Is this a group of seizures with one timestamp? 
                "	1, Yes | 2, No, this is an individual seizure, and PART OF A CLUSTER. | 0, No, this is an isolated seizure, NOT part of a cluster. | 3, Not Applicable-Because EEG Not Available, Not a Seizure, Not on Recording												
                '''
                szr_cluster = patient_data[szr_cluster_field]


                szr_semiology = get_szr_semiology(patient_data, patient_id, event_name, redcap_repeat_instance)

                if szr_semiology[1] != 'szr free':
                    eeg_szr_onset_ut, eeg_szr_offset_ut, correct_onoffset_flag =  get_eeg_szr_onset_offset_ut(patient_data, patient_id, event_name, redcap_repeat_instance)

                    if eeg_szr_onset_ut != 0 and eeg_szr_offset_ut!= 0:
                        szr = {}

                        szr['eeg_szr_onset_ut'] = eeg_szr_onset_ut
                        szr['eeg_szr_onset_t'] = get_datetime(eeg_szr_onset_ut)
                        szr['eeg_szr_offset_ut'] = eeg_szr_offset_ut
                        szr['eeg_szr_offset_t'] = get_datetime(eeg_szr_offset_ut)

                        szr['szr_used_ibm_flag'] = szr_used_ibm_flag
                        szr['szr_cluster']=szr_cluster

                        szr['unique_event_name'] = unique_event_name
                        szr['redcap_repeat_instrument'] = redcap_repeat_instrument
                        szr['redcap_repeat_instance'] = redcap_repeat_instance
                        szr['correct_onoffset_flag'] = correct_onoffset_flag

                        szr['szr_semiology'] = szr_semiology
                        szrs.append(szr)
                    else:
                        print('Error! No EEG onset or offset was found for patient ID "%s"' % patient_id)
                else:
                    print('"Not a seizure" was found for patient ID "%s"' % szr_semiology[0])

    return szrs


def update_szr_usage(redcap_project, patient_id, wrst_placements,szrs,wrst_data_dicts,wrst_data_label_dicts):
    # for those skipped wristband placement, modify szr to be "not used"
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

        # go through all the szrs, find their correspoding data,
        # for clustered szr, skip the whole session by setting the 'labelled' to be fause
        for szr in szrs:
            eeg_szr_onset_ut = szr['eeg_szr_onset_ut']
            eeg_szr_offset_ut = szr['eeg_szr_offset_ut']
            eeg_szr_onset_t = szr['eeg_szr_onset_t']
            eeg_szr_offset_t = szr['eeg_szr_offset_t']
            szr_duration = eeg_szr_offset_ut - eeg_szr_onset_ut

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
                    pass
                else:
                    # if found, then locate its data label dictionary
                    wrst_data_index = wrst_data_dict['wrst_data_index']
                    wrst_data_label_dict = wrst_data_label_dicts[wrst_data_index]

                    wrst_label_flag = wrst_data_label_dict['labelled']
                    # wrst_loc = wrst_data_label_dict['location']

                    if wrst_label_flag== False:
                        # get number of used location

                        # uncheck the corresponding wrist loc
                        upload_szr_wrst_loc(redcap_project, patient_id,
                                            szr['unique_event_name'],
                                            szr['redcap_repeat_instrument'],
                                            szr['redcap_repeat_instance'],
                                            wrst_loc, 0)

                        # get the usage status
                        usage_flag = get_szr_usage(redcap_project, patient_id,
                                            szr['unique_event_name'],
                                            szr['redcap_repeat_instrument'],
                                            szr['redcap_repeat_instance'])

                        if not usage_flag:
                            # szr_wrst_loc	0, Not used | 1, Left Wrist | 2, Left Ankle | 3, Right Wrist | 4, Right Ankle | 5, Unknown | 6, Right Unknown | 7, Left Unknown
                            upload_szr_wrst_loc(redcap_project, patient_id,
                                                szr['unique_event_name'],
                                                szr['redcap_repeat_instrument'],
                                                szr['redcap_repeat_instance'],
                                                'not used',1)

                            print('Event: %s, seizure: %s not used due to wrst_placement instance: %d are skipped' % (
                            wrst_placement['event_name'], szr['szr_semiology'][0],wrst_data_label_dict['redcap_repeat_instance']))

def get_szr_usage(project, patient_id,input_unique_event_name,
                                            input_redcap_repeat_instrument,
                                            input_redcap_repeat_instance):
    events = project.events

    ids_of_interest = ['redcap_event_name', patient_id]
    patient_data_all = project.export_records(records=ids_of_interest)
    if not patient_data_all:
        print('Error! No data was found. Please check your patient ID "%s"' % patient_id)
        return

    szrs = []
    # extract each event's data
    for event in events:

        unique_event_name = event['unique_event_name']
        # event_name = event['event_name']
        patient_data_list = get_events_data(patient_data_all, event)

        if not patient_data_list:  # no test date found
            continue

        # first, get all the onset/offset
        for patient_data in patient_data_list:

            redcap_repeat_instrument = patient_data['redcap_repeat_instrument']
            redcap_repeat_instance = patient_data['redcap_repeat_instance']

            if input_unique_event_name == unique_event_name and \
                    redcap_repeat_instrument == input_redcap_repeat_instrument and redcap_repeat_instance==input_redcap_repeat_instance:

                if (patient_data['szr_wrst_loc___1']=='0' and \
                    patient_data['szr_wrst_loc___2'] =='0' and \
                    patient_data['szr_wrst_loc___3'] =='0' and \
                    patient_data['szr_wrst_loc___4'] =='0' and \
                    patient_data['szr_wrst_loc___5'] =='0' and \
                    patient_data['szr_wrst_loc___6'] =='0' and \
                    patient_data['szr_wrst_loc___7'] =='0' and \
                    patient_data['szr_wrst_loc___8'] =='0' and \
                    patient_data['szr_wrst_loc___9'] =='0') :
                    usage_flag = False
                else:
                    usage_flag = True
                break

    return usage_flag