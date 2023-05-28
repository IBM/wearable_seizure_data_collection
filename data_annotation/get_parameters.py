import os
import platform
import argparse
from redcap import Project
from pathlib import Path

def get_parameters():

    parser = argparse.ArgumentParser(description='BCH Data annotation')

    if platform.system() == 'Linux':
        parser.add_argument('-r','--root_dir', default='/bigdata/datasets/REDCap_202109',
                            help='path to output prediction')
        parser.add_argument('-o', '--out_dir', default='/bigdata/datasets/REDCap_202109_out',
                            help='path to output prediction')
    elif platform.system() == 'Darwin':
        parser.add_argument('-r','--root_dir', default=os.path.join(Path.home(),'datasets/bch/REDCap_202109'),
                            help='path to output prediction')
        parser.add_argument('-o', '--out_dir', default=os.path.join(Path.home(),'datasets/bch/REDCap_202109_out'),
                            help='path to output prediction')
    else:
        print('Unknown OS platform %s' % platform.system())
        exit()

    parser.add_argument('-s','--strict_flag', default=0, type=int,
                        help='1: strict which only accept those with start timing error adjustment ')
    parser.add_argument('-f', '--offline_clock_err', default=-13.0,  type=float,
                        help='offline clock err in Hz')

    parser.add_argument('-e', '--enable_clock_compenstate', default=1, type=int,
                        help='maximum cpu number allowed for parallel processing')

    parser.add_argument('--inc_szr_cluster', default=1, type=int,
                        help='1: include szr cluster')

    parser.add_argument('--szr_cluster_win', default=0, type=int,
                        help='default protection window of szr cluster')

    parser.add_argument('--pre_win', default=20, type=int,
                        help='pre window size')

    parser.add_argument('--post_win', default=20, type=int,
                        help='post window size')

    parser.add_argument('--api_url', type=str, default='https://redcap.tch.harvard.edu/redcap_edc/api/',
                        help='Redcap API\'s url')
    # Development: Duplicate
    # parser.add_argument('--api_key', type=str, default='FF936606363B280BB4AB8ACF2AA1278E',

    # sandbox:
    parser.add_argument('--api_key', type=str, default='EF8B5CABBCCEE7C0B007F0F688AD8626',

    # release
    # parser.add_argument('--api_key', type=str, default='4EB24D1F3BBB3C72AEE8D28C07C49627',
                        help='Redcap API\'s key')

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

    args = parser.parse_args()

    # strict means use strict rule to find suitable data
    if args.strict_flag==0:
        strict_flag = False
    else:
        strict_flag = True
    if args.enable_clock_compenstate==0:
        enable_clock_compenstate = False
    else:
        enable_clock_compenstate = True

    pos_inf = 99999999999999999  # positive infinity
    neg_inf = -99999999999999999  # negtive infinity

    # sensors = ['ACC', 'BVP', 'EDA', 'HR', 'IBI', 'TEMP']
    # skip HR, IBI to save space
    sensors = ['ACC', 'BVP', 'EDA', 'TEMP']

    wrst_raw_data_dir = os.path.join(args.out_dir, 'raw_data')

    if strict_flag:
        # dir to store the data label
        extension_start = 2  # in seconds
        extension_end = 60  # in seconds
        skip_freq_szr_event_flag = True
        # threshold of the timing error between eeg and wristband start time, unit: second
        # timing_err_thre = 20
        left_right_err_diff_thre = 5  # left and right timing error will be no more than that. If it is, use the smaller one.
        wrst_start_timing_err_thre = pos_inf
        wrst_eeg_start_timing_err_thre = pos_inf
        align_left_right_timing_flag = True
        if enable_clock_compenstate:
            extension_start = 5  # in seconds
            extension_end = 5  # in seconds
            wrst_data_label_dir = 'case4_strict_label_s' + str(extension_start) + '_e' + str(extension_end)
        else:
            wrst_data_label_dir = 'strict_label_s' + str(extension_start) + '_e' + str(extension_end)

    else:
        # dir to store the data label
        extension_start = args.pre_win  # in seconds
        extension_end = 40  # in seconds
        skip_freq_szr_event_flag = True
        # threshold of the timing error between eeg and wristband start time, unit: second
        # timing_err_thre = 20
        left_right_err_diff_thre = 5  # left and right timing error will be no more than that. If it is, use the smaller one.
        wrst_start_timing_err_thre = pos_inf
        wrst_eeg_start_timing_err_thre = pos_inf
        align_left_right_timing_flag = True
        if enable_clock_compenstate:
            extension_end = args.post_win  # in seconds
            wrst_data_label_dir = 'case4_non_strict_label_s' + str(extension_start) + '_e' + str(
                extension_end)
        else:
            wrst_data_label_dir = 'non_strict_label_s' + str(extension_start) + '_e' + str(extension_end)

    if args.inc_szr_cluster!=0:
        wrst_data_label_dir = wrst_data_label_dir +'_szr_cluster_win'+ str(args.szr_cluster_win)

    wrst_data_label_dir = os.path.join(args.out_dir,wrst_data_label_dir)

    os.makedirs(wrst_data_label_dir, 0o777, True)
    log_file_dir = os.path.join(wrst_data_label_dir, 'log.txt')

    args.extension_start = extension_start
    args.extension_end = extension_end
    # args.timing_err_thre = timing_err_thre
    args.left_right_err_diff_thre = left_right_err_diff_thre
    args.wrst_start_timing_err_thre = wrst_start_timing_err_thre
    args.wrst_eeg_start_timing_err_thre = wrst_eeg_start_timing_err_thre
    args.align_left_right_timing_flag = align_left_right_timing_flag
    args.wrst_data_label_dir = wrst_data_label_dir

    args.pos_inf = pos_inf
    args.neg_inf = neg_inf
    args.sensors = sensors
    args.wrst_raw_data_dir = wrst_raw_data_dir
    args.log_file_dir = log_file_dir

    args.project =  project
    return args