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
    Define constants
'''

POS_BIG_NUM = 9999999999999999999
invalid_t = '1900-01-01 00:00'
invalid_ut = -2208971040.0 #For intentional empty time, we use “01-01-1900 00:00” or “01-01-1900 00:00:00” to indicate

# define error code
# wrst only: 1xx; # eeg only: 2xx; # between wrst and eeg: 3xx
# error between wristband start time in csv(1st line's unix time) and wristband place time in col g/h is too large
WRST_START_ERR = 101
# error between wristband end time in csv(1st line's unix time+duration) and wristband removal time in col i/j is too large
WRST_END_ERR = 102
# wristband place time in col g/h is not consist with folder name in dataset
WRST_LOC_FOLDER_ERR = 103
# wristband doesn't have time in tags.csv
WRST_NO_TAG = 104
# wristband location in col e/f is not consist with wrist place/rmv time in col g/h/i/j
WRST_LOC_TIME_ERR = 105
# wristband's date folder doesn't exist
WRST_WRONG_DATE_FOLDER = 106
# didn't find wristband sensor data's start unix time in temp.csv
WRST_NO_START_TIME = 107
#Incorrect wristband DateTime format in excel col g/h/i/j
WRST_WRONG_DATETIME_EXCEL =  108
# can not find seizure in wristband signal
WRST_SESSION_NOT_FOUND = 109
# no wrstband location are specified
WRST_NO_LOCATION = 111
# overlapped wrist placement
WRST_OVERLAP = 112
# too early and too late may indicate wrong wristband signal file
WRST_START_TOO_EARLY = 113
WRST_START_TOO_LATE = 114
WRST_WRONG_ZIP_FILE_ID = 115

# seizure without onset time
SZR_NO_ONSET = 201
# seizure without offset time and LTM duration
SZR_NO_OFFSET = 202
# EEG has no start time (can't search which EEG test session, in this case, has to search wrst place/rmv time, maybe search both)
EEG_NO_START = 203
# There should never be a 99:99 in Column S and then a timestamp in Column R. That would indicate a mistake because if the video is not available then we would not have been able to extract a video timestamp.
# Also for Column R is not valid when Column S=1
EEG_SR_MISMATCH = 204
# Col L/M has wrong value
EEG_WRONG_LM = 205
# Col N/O has wrong value
EEG_WRONG_NO = 206
# Col S has wrong value
EEG_WRONG_S = 207
# Col R has wrong value
EEG_WRONG_R = 208
# can not find seizure in EEG datetime scope
EEG_SESSION_NOT_FOUND = 209
# EEG has wrong duration
SZR_WRONG_DUR = 210
# EEG has overlapped annotation
SZR_OVERLAP = 211
# EEG onset is earlier than start button press time
SZR_EARLY_ONSET = 212
# EEG offset is later than end button press time
SZR_LATE_OFFSET = 213


# error between wristband start time in csv(1st line's unix time) and eeg start time in excel is too large
WRST_EEG_START_ERR = 301
# error between wristband's button press time in tags.csv and eeg start time in excel is too large
WRST_EEG_START_TIMING_ERR = 302
# wristband location in col e/f is not consist with eeg artifact/btn press time in col l/m/n/o
WRST_LOC_EEG_TIME_ERR = 303
# error between wristband's button press time in tags.csv and eeg start time in excel is too large
WRST_EEG_END_TIMING_ERR = 304

# patient test session(PTS) related
PTS_NO_TEST_DATE = 401
PTS_WRONG_PLACE_REMOVAL_TIME = 402


###################################################################################################################
# Define Red Cap Field to be easily change to new name
####################################################################################################################

# instruments_name
demo_instru = 'demographics'
pts_instru = 'patient_test_sessions_metadata'
wrst_place_instru = 'wristband_placement'# 'wristband_placement_repeat_eventnew'
szr_anno_instru = 'seizures_at_enrollment_repeat_events' # 'seizures_at_enrollment_repeat_event'
szr_in_general_instru = 'number_of_seizures_in_general_during_admissions' # 'number_of_seizures_in_general_during_admission'

# demographics related
export_flag_field = 'project_pt'
first_enroll_age_field = 'first_enroll_age'
first_enroll_date_field = 'first_enroll_date'
ibm_flag_idx = 1

# pts_metadata related
enroll_age_field = 'enroll_age'
gender_field = 'sex'
enroll_date_field = 'enroll_date'
wrst_type_field = 'type_wrist'
exclude_enroll_flag_field = 'data_exclude'

# wristband related
patient_rm_num_field = 'room_number'
wrst_id_field = 'wrist_id'
wrst_on_field = 'wrist_on'
wrst_off_field = 'wrist_off'
wrst_on_date_field = 'wrist_on_date'
wrst_off_date_field = 'wrist_off_date'
wrst_location_field = 'wrist_loc'
wrist_mov_flag_field = 'wrist_mov'
other_wrist_loc_field = 'other_wrist_loc'
wrst_off_flag_field = 'wrist_off_flag'
eeg_btn_prs_start_t_field = 'start_eeg_btn'
eeg_btn_prs_end_t_field = 'end_eeg_btn'
video_btn_prs_start_t_field = 'start_video_btn'
video_btn_prs_end_t_field = 'end_video_btn'
start_timing_sync_src_flag_field = 'start_sync_src_flag'
end_timing_sync_src_flag_field = 'end_sync_src_flag'
wrst_download_flag_field = 'sig_download' # 1: downloaded, 0: not downloaded
sig_usage_flag_field = 'sig_usage' # 1: use; 0: don't use
full_timing_sync_flag_field = 'full_timing_sync_flag'
#wrst_start_t_field = 'wrst_start_t'
#wrst_end_t_field = 'wrst_end_t'
wrst_btn_prs_start_t_field = 'wrst_btn_prs_start_t'
wrst_btn_prs_end_t_field = 'wrst_btn_prs_end_t'
wrst_start_t_field = 'wrst_start_t'
wrst_end_t_field = 'wrst_end_t'

wrst_dur_field = 'wrst_duration'
start_timing_err_field = 'start_timing_err'
end_timing_err_field = 'end_timing_err'
timing_drift_field = 'timing_drift'
err_per_sec_field = 'err_per_sec'
#notes_place_ibm_field = 'notes_place_ibm'
wrst_log_field = 'wrst_log'
wrst_usage_field = 'wrst_usage'
wrst_case_field = 'wrst_case'
'''
1, Ideal case (No Timing Info)
2, With Start Timing Adjust
3, With Start/End Timing Adjust
'''
wrst_not_use_reason_list = ['No raw data','Raw data too short','Missing EEG onset/offset definition','Not used for other reasons']
wrst_not_use_reasons_field = 'wrst_not_use_reasons'

#wrst_loc_list = ['Left Wrist', 'Left Ankle', 'Right Wrist', 'Right Ankle', 'Unknown', 'Not available']

# 1, Left Wrist
# 2, Left Ankle
# 3, Right Wrist
# 4, Right Ankle
# 5, Unknown
# 6, Right Unknown
# 7, Left Unknown
# 8, Unknown wrist
# 9, Unknown ankle
wrst_loc_list = ['Left Wrist', 'Left Ankle', 'Right Wrist', 'Right Ankle', 'Unk', 'Right Unk', 'Left Unk', 'Unk wrist', 'Unk ankle']


# seizure annotation related
eeg_video_avai_field = 'eeg_video_avai'
sz_checked_field = 'sz_checked'
eeg_szr_onset_field = 'eeg_onset'
eeg_szr_offset_field = 'eeg_offset'
sei_dura_cal_field = 'sei_dura_cal'
dura_ltm_avai_field = 'dura_ltm_avai'
dura_ltm_field = 'dura_ltm'
sz_semiology_field = 'sz_semiology'
sz_type_enroll_old_field = 'sz_type_enroll_old'
subclinic_sz_field = 'subclinic_sz'


szr_cluster_field = 'seizure_cluster'
sz_type_enroll_new_field = 'sz_type_enroll_new'
'''
1, Focal onset
2, Generalized onset
4, Unknown onset/Unclassified onset
a szr without proof from EEG, will discard the corresponding wristband session -> 5, EEG Not Available-EEG Not Available 
treat as background -> 6, Not A Seizure/ Or Is a seizure and not on wristband recording
'''

subclinic_sz_field = 'subclinic_sz'
'''
available for 1,2,4
'''
onset_mov_field = 'onset_mov'
'''
1, Motor
2, Non-motor
3, Not Available/Patient off Camera-EEG Video
4, Unclassified-Unable to clinically classify
'''
focal_aware_field = 'focal_aware'
'''
1, Aware
2, Impaired awareness
3, Unclassified-Clinically you can't classify
4, Not Applicable for: Focal To Bilateral Tonic-Clonic
'''
focal_motor_field = 'focal_motor'
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
focal_non_mo_field = 'focal_non_mo'
'''
1, Autonomic
2, Behavior arrest
3, Cognitive
4, Emotional
5, Sensory
6, Unclassified-Unable to clinically classify
'''
generalized_motor_field = 'generalized_motor'
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
generalized_non_motor_field = 'generalized_non_motor'
'''
1, Tonic-clonic
2, Epileptic spasms
3, Unclassified-Unable to clinically classify
'''
unknown_motor_manif_field = 'unknown_motor_manif'
'''
1, Tonic-clonic
2, Epileptic spasms
3, Unclassified-Unable to clinically classify
'''
un_nonmotor_manif_field = 'un_nonmotor_manif'
'''
1, Yes
0, No 
'''
gtc_flag_field = 'gtc'
gtc_class_field = 'gtc_class'
notes_sz_type_field = 'notes_sz_type'

'''
tonic_onset
clonic_onset
clonic_offset
tonic_duration
clonic_duration
clinical_onset
clinical_ons
clinical_off
pgess
pges_start
pges_end
suppression_duration
'''

szr_wrst_loc_field = 'szr_wrst_loc'
szr_log_field = 'szr_log'


szr_label = ['szr free','szr','no eeg']
szr_base_type_list = ['focal', 'gnr', 'invalid', 'unk/uncls']  # 9
szr_focal_aware_type_list = ['aware', 'impaired', 'uncls', 'FBTC']  # 8
szr_motor_type_list = ['motor', 'non-motor', 'off camera', 'uncls']  # 10

# focal base type
'''
focal_motor	seizures_at_enrollment_repeat_events		radio	Focal onset, motor	
1, Automatisms 
| 2, Atonic 
| 3, Clonic 
| 4, Epileptic spasms 
| 5, Hyperkinetic 
| 6, Myoclonic 
| 7, Tonic 
| 8, Bilateral tonic-clonic 
| 9, Unclassified-Unable to clinically classify
'''

szr_focal_motor_sub_type_list = ['Automatisms','Atonic','Clonic','Epileptic spasms','Hyperkinetic','Myoclonic','Tonic','FBTC','Unclassified']
'''											
focal_non_mo	seizures_at_enrollment_repeat_events		radio	Focal onset, nonmotor	
1, Autonomic 
| 2, Behavior arrest 
| 3, Cognitive 
| 4, Emotional 
| 5, Sensory 
| 6, Unclassified-Unable to clinically classify					
'''
szr_focal_non_motor_sub_type_list = ['Autonomic', 'Behavior arrest', 'Cognitive', 'Emotional', 'Sensory',
                                     'Unclassified']
'''
generalized_motor	seizures_at_enrollment_repeat_events		radio	Generalized onset, motor	
1, Tonic-clonic 
| 2, Clonic 
| 3, Tonic 
| 4, Myoclonic 
| 5, Myoclonic-tonic-clonic 
| 6, Myoclonic-atonic 
| 7, Atonic 
| 8, Epileptic spasms 
| 9, Unclassified-Unable to clinically classify					
'''
# generalised base type
szr_gnr_motor_sub_type_list = ['Tonic-clonic', 'Clonic', 'Tonic', 'Myoclonic', 'Myoclonic-TC', 'Myoclonic-atonic',
                               'Atonic', 'Epileptic spasms', 'Unclassified']

'''
generalized_non_motor
1, Typical absence 
| 2, Atypical absence 
| 3, Absence with myoclonus 
| 4, Absence with eyelid myoclonia 
| 5, Unclassified-Unable to clinically classify						
'''
szr_gnr_non_motor_sub_type_list = ['Typical abs', 'Atypical abs', 'Abs w/ myoclonus',' Abs w/ eyelid my','Unclassified']

# for unknown base type
'''
unknown_motor_manif	seizures_at_enrollment_repeat_events		radio	Unknown onset, motor	
1, Tonic-clonic 
| 2, Epileptic spasms 
| 3, Unclassified-Unable to clinically classify												
'''

szr_unk_motor_sub_type_list = ['Tonic-clonic', 'Epileptic spasms', 'Unclassified']
'''
un_nonmotor_manif	seizures_at_enrollment_repeat_events		yesno	Unknown onset, nonmotor (behavior arrest)		The only manifestation of this type is behavior arrest.					[sz_type_enroll_new] = '3' and [onset_mov] = '2' and [subclinic_sz] = '0'						
'''
szr_unk_non_motor_sub_type_list = ['Behavioral arrest', 'Unclassified']

'''
    1, Focal onset | 2, Generalized onset | 4, Unknown/Unclassified onset
    | 5, EEG Not Available-EEG Not Available because you need the EEG to answer this question and all the other questions below. No other questions should open up. GAME OVER.
    | 6, Not A Seizure  | 7, Seizure not on wristband
    '''
sz_type_enroll_new_list = ['Focal','Generalized','','Unknown/Unclassified onset','EEG Not Available','Not A Seizure','Seizure not on wristband']


'''
seizure_cluster	"Is this a group of seizures with one timestamp? 
1, Yes 
2, No, this is an individual seizure, and PART OF A CLUSTER. 
0, No, this is an isolated seizure, NOT part of a cluster. 
3, Not Applicable-Because EEG Not Available, Not a Seizure, Not on Recording
'''
szr_cluster_list = ['single seizure','seizure cluster','single seizure in cluster','not applicable']
