import os
import re
import pickle
import platform
import numpy as np
import matplotlib.pyplot as plt
import argparse

# function to return the first element of the
# two elements passed as the parameter
def sortFirst(val):
    return val[0]

parser = argparse.ArgumentParser(description='BCH Data Training')

if platform.system() == 'Linux':
    parser.add_argument('-r','--root_dir', default='/bigdata/datasets/bch/REDCap_202109',
                        help='path to output prediction')
    parser.add_argument('-o', '--out_dir', default='/bigdata/datasets/bch/REDCap_202109_out',
                        help='path to output prediction')
elif platform.system() == 'Darwin':
    parser.add_argument('-r','--root_dir', default='/Users/jbtang/datasets/bch/REDCap_202109',
                        help='path to output prediction')
    parser.add_argument('-o', '--out_dir', default='/Users/jbtang/datasets/bch/REDCap_202109_out',
                        help='path to output prediction')
else:
    print('Unknown OS platform %s' % platform.system())
    exit()

parser.add_argument('-s','--strict_flag', default=0, type=int,
                    help='matching start str, empty means no limitation')
parser.add_argument('-f', '--offline_clock_err', default=-13.0,  type=float,
                    help='maximum cpu number allowed for parallel processing')

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


args = parser.parse_args()

root_dir = args.root_dir
out_dir = args.out_dir
offline_clock_err = args.offline_clock_err

plot_flag = False

# strict means use strict rule to find suitable data
if args.strict_flag==0:
    strict_flag = False
else:
    strict_flag = True
if args.enable_clock_compenstate==0:
    enable_clock_compenstate = False
else:
    enable_clock_compenstate = True

print('root_dir=%s'%root_dir)
print('out_dir=%s'%out_dir)
wrst_raw_data_dir = os.path.join(out_dir, 'raw_data')
# dir to store the data label

#strict_flag = False
#enable_clock_compenstate = False
if strict_flag:
    if enable_clock_compenstate:
        extension_start = 5  # in seconds
        extension_end = 5  # in seconds
        wrst_data_label_dir_name = 'case4_strict_label_s' + str(extension_start) + '_e' + str(extension_end)
    else:
        extension_start = 2  # in seconds
        extension_end = 20  # in seconds
        wrst_data_label_dir_name = 'strict_label_s' + str(extension_start) + '_e' + str(extension_end)
else:
    if enable_clock_compenstate:
        extension_start = 20  # in seconds
        extension_end = 20  # in seconds
        wrst_data_label_dir_name = 'case4_non_strict_label_s' + str(extension_start) + '_e' + str(extension_end)
    else:
        extension_start = 20  # in secondsdux
        extension_end = 40  # in seconds
        wrst_data_label_dir_name = 'non_strict_label_s' + str(extension_start) + '_e' + str(extension_end)


if args.inc_szr_cluster!=0:
    wrst_data_label_dir = wrst_data_label_dir_name +'_szr_cluster_win'+ str(args.szr_cluster_win)

wrst_data_label_dir = os.path.join(args.out_dir,wrst_data_label_dir)

sensors = ['ACC', 'BVP', 'EDA', 'HR', 'IBI', 'TEMP']

# if want to plot all the patients
patient_dir_pattern = '^C[0-9]{3}'
# if only want to plot specific patient
# patient_dir_pattern = '^C358'
# patient_dir_pattern = '^C278'
patient_dir_re = re.compile(patient_dir_pattern)

# mkdir for visualisation
visual_path = 'visualisation'
os.makedirs(visual_path, 0o777, True)

szr_statistics_file = os.path.join(wrst_data_label_dir,'szr_statistics.csv')
patient_szr_num_per_test_date_file = open(szr_statistics_file, 'w')
patient_szr_num_per_test_date_file.write('Patient ID,Test Date,Location,Seizure Num,Seizure Dur\n')
patient_szr_num_per_test_date_file.close()

patient_total_szr_num_file_name = os.path.join(wrst_data_label_dir,'total_szr_statistics.csv')
patient_total_szr_num_file = open(patient_total_szr_num_file_name, 'w')
patient_total_szr_num_file.write('Patient ID,Seizure Num,Seizure Dur,Total Dur,BVP data points,ACC data points,EDA data points,TEMP data points,HR data points\n')
patient_total_szr_num_file.close()

single_szr_statistics_file = os.path.join(wrst_data_label_dir,'single_szr_statistics.csv')
single_szr_statistics_file_hdl = open(single_szr_statistics_file, 'w')
single_szr_statistics_file_hdl.write('Patient ID,Test Date,Location,Seizure Num,Seizure Idx, Seizure Dur, szr_cluster\n')
single_szr_statistics_file_hdl.close()


total_dur = 0  # seconds
total_dur_labeled = 0
total_dur_with_szr_labeled = 0
total_szr_dur = 0
total_szr_num = 0

# total_left_szr_dur = 0  # seconds
# total_right_szr_dur = 0  # seconds
total_left_wrst_dur = 0  #
total_right_wrst_dur = 0  #

total_patient_num_with_szr = 0  #
patient_list_with_szr=[]

seizure_len =[]



for wrst_data_label_file in sorted(os.listdir(wrst_data_label_dir)):
    if wrst_data_label_file.endswith(".pkl") and patient_dir_re.match(wrst_data_label_file):
        patient_id = wrst_data_label_file[:-4:]
        wrst_data_label_file_name = os.path.join(wrst_data_label_dir, wrst_data_label_file)
        pickling_on = open(wrst_data_label_file_name, "rb")
        wrst_data_label_dicts = pickle.load(pickling_on)
        pickling_on.close()

        # load data and plot
        wrst_data_file_name = os.path.join(wrst_raw_data_dir, wrst_data_label_file)
        pickling_on = open(wrst_data_file_name, "rb")
        wrst_data_dicts = pickle.load(pickling_on)
        pickling_on.close()

        patient_total_szr_num = 0 # print out all not labelled data
        patient_total_szr_dur = 0


        patient_total_dur = 0

        for wrst_data_label_dict in wrst_data_label_dicts:
            total_dur += len(wrst_data_label_dict['label'])
            if  wrst_data_label_dict['labelled']:
                total_dur_labeled += len(wrst_data_label_dict['label'])

            if not wrst_data_label_dict['labelled']:
                print('Not labelled: Patient %s at %s, start_t %s, end_t %s due to %s'
                      % (wrst_data_label_file, wrst_data_label_dict['location'], wrst_data_label_dict['start_t'],
                         wrst_data_label_dict['end_t'], wrst_data_label_dict['issues']))


            else:
                # find out corresponding wrst_data_dicts
                wrst_data_index = wrst_data_label_dict['wrst_data_index']
                labels = wrst_data_label_dict['label']

                # diff to find start and end
                # diff_labels = np.diff(labels, axis=0)
                # start = np.nonzero(diff_labels > 0) +1
                # end = np.nonzero(diff_labels < 0) +1

                # plot seizures
                szr_idx = 0
                seizures = wrst_data_label_dict['seizures']
                # seizures.sort(key=sortFirst)
                seizure_num = wrst_data_label_dict['seizure_num']
                patient_total_szr_num += seizure_num
                patient_total_dur += len(wrst_data_label_dict['label'])

                if wrst_data_label_dict['location'].startswith('left'):
                    total_left_wrst_dur += len(wrst_data_label_dict['label'])
                elif wrst_data_label_dict['location'].startswith('right'):
                    total_right_wrst_dur += len(wrst_data_label_dict['label'])
                else:
                    print('ERROR location %s' % (wrst_data_label_dict['location']))

                if seizure_num==0:
                    print('Labelled but no seizure: Patient %s at %s, start_t %s, end_t %s due to %s'
                      % (wrst_data_label_file, wrst_data_label_dict['location'], wrst_data_label_dict['start_t'],
                         wrst_data_label_dict['end_t'], wrst_data_label_dict['issues']))

                    print('Patient ID %s, Test Date %s, Location %s, Seizure Num %d, Seizure Dur %d seconds' % (patient_id, wrst_data_label_dict['date'], wrst_data_label_dict['location'], seizure_num, 0))
                    patient_szr_num_per_test_date_file = open(szr_statistics_file, 'a+')
                    patient_szr_num_per_test_date_file.write('%s, %s, %s, %d, %d \n' % (patient_id, wrst_data_label_dict['date'], wrst_data_label_dict['location'], seizure_num, 0))
                    patient_szr_num_per_test_date_file.close()
                    continue

                wrst_data_dict = wrst_data_dicts[wrst_data_index]
                date = wrst_data_dict['date']
                location = wrst_data_dict['location']
                patient_path = os.path.join(visual_path,wrst_data_label_dir_name,patient_id,date,location)
                os.makedirs(patient_path, 0o777, True)

                # plot whole
                #fig_all = plt.figure()
                patient_szr_dur = 0
                for seizure in seizures:

                    patient_szr_dur += (seizure[1] - seizure[0])
                    single_szr_dur = (seizure[1] - seizure[0])
                    szr_cluster = wrst_data_label_dict['szr_cluster'][szr_idx]
                    szr_idx += 1

                    seizure_len.append(single_szr_dur)
                    single_szr_statistics_file_hdl = open(single_szr_statistics_file, 'a+')
                    single_szr_statistics_file_hdl.write('%s, %s, %s, %d, %d, %d, %s \n' % (
                        patient_id, wrst_data_label_dict['date'], wrst_data_label_dict['location'], seizure_num,szr_idx,
                        single_szr_dur-40, szr_cluster ))
                    single_szr_statistics_file_hdl.close()


                    if plot_flag:
                        fig = plt.figure()
                        sensor = 'BVP'
                        sensor_start = seizure[0] * wrst_data_dict[sensor + '_fs']
                        sensor_end = seizure[1] * wrst_data_dict[sensor + '_fs']
                        sensor_data = wrst_data_dict[sensor][sensor_start:sensor_end]
                        t = np.linspace(seizure[0], seizure[1], sensor_end - sensor_start)
                        ax = fig.add_subplot(211)
                        ax.plot(t, sensor_data)
                        ax.title.set_text(sensor)
                        ax.set_ylabel('nano Watt')
                        #ax.set_xlabel('time(Seconds)')
                        #ax.set_tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
                        #ax.set_bottom('off')

                        sensor = 'EDA'
                        ax = fig.add_subplot(212)
                        sensor_start = seizure[0] * wrst_data_dict[sensor + '_fs']
                        sensor_end = seizure[1] * wrst_data_dict[sensor + '_fs']
                        sensor_data = wrst_data_dict[sensor][sensor_start:sensor_end]
                        t = np.linspace(seizure[0], seizure[1], sensor_end - sensor_start)
                        ax.plot(t, sensor_data)
                        ax.title.set_text(sensor)
                        ax.set_ylabel('us')
                        ax.set_xlabel('time(Seconds)')

                        fig_name = 'seizure_' +  str(szr_idx) + '.png'
                        fig_name_pdf = 'no_seizure_' + str(szr_idx) + '.pdf'
                        plt.tight_layout()
                        plt.savefig(os.path.join(patient_path,fig_name))
                        plt.savefig(os.path.join(patient_path, fig_name_pdf), bbox_inches='tight')

                        #plt.show()
                        plt.close()

                patient_total_szr_dur += patient_szr_dur


                print('Patient ID %s, Test Date %s, Location %s, Seizure Num %d, Seizure Dur %s seconds' % (
                    patient_id, wrst_data_label_dict['date'], wrst_data_label_dict['location'], seizure_num, patient_szr_dur))
                patient_szr_num_per_test_date_file = open(szr_statistics_file, 'a+')
                patient_szr_num_per_test_date_file.write('%s, %s, %s, %d, %d \n' % (
                    patient_id, wrst_data_label_dict['date'], wrst_data_label_dict['location'], seizure_num, patient_szr_dur))
                patient_szr_num_per_test_date_file.close()

                # plot non seizures
                if plot_flag:
                    min_non_szr_dur = 100 #seconds

                    for ii in range(len(seizures)-1):
                        fig = plt.figure()
                        sensor = 'BVP'
                        ax = fig.add_subplot(211)

                        sensor_start = (seizures[ii][1]+1) * wrst_data_dict[sensor + '_fs']
                        sensor_end = (seizures[ii+1][0]-1) * wrst_data_dict[sensor + '_fs']

                        if sensor_start>sensor_end:
                            print('No Szr Gap: Patient %s at %s, start_t %s, end_t %s due to %s'
                                  % (
                                  wrst_data_label_file, wrst_data_label_dict['location'], wrst_data_label_dict['start_t'],
                                  wrst_data_label_dict['end_t'], wrst_data_label_dict['issues']))
                            continue

                        sensor_data = wrst_data_dict[sensor][sensor_start:sensor_end]
                        t = np.linspace(seizures[ii][1]+1,seizures[ii+1][0]-1, sensor_end-sensor_start)
                        ax.plot(t, sensor_data)
                        ax.title.set_text(sensor)
                        ax.set_ylabel('nano Watt')
                        #ax.set_xlabel('time(Seconds)')

                        sensor = 'EDA'
                        ax = fig.add_subplot(212)
                        sensor_start = (seizures[ii][1] + 1) * wrst_data_dict[sensor + '_fs']
                        sensor_end = (seizures[ii + 1][0] - 1) * wrst_data_dict[sensor + '_fs']

                        sensor_data = wrst_data_dict[sensor][sensor_start:sensor_end]
                        t = np.linspace(seizures[ii][1] + 1, seizures[ii + 1][0] - 1, sensor_end - sensor_start)
                        ax.plot(t, sensor_data)
                        ax.title.set_text(sensor)
                        ax.set_ylabel('us')
                        ax.set_xlabel('time(Seconds)')

                        fig_name = 'no_seizure_' + str(ii) + '.png'
                        fig_name_pdf = 'no_seizure_' + str(ii) + '.pdf'
                        plt.tight_layout()
                        plt.savefig(os.path.join(patient_path,fig_name))
                        plt.savefig(os.path.join(patient_path,fig_name_pdf), bbox_inches='tight')

                        #plt.show()
                        plt.close()
        if patient_total_dur>0:
            patient_total_szr_num_file = open(patient_total_szr_num_file_name, 'a+')
            patient_total_szr_num_file.write('%s,  %d, %d, %d, %d, %d, %d, %d, %d \n'
                                             % (patient_id, patient_total_szr_num,  patient_total_szr_dur, patient_total_dur,
                                                patient_total_dur*64,patient_total_dur*96,patient_total_dur*4,patient_total_dur*4,patient_total_dur))
            patient_szr_num_per_test_date_file.close()

        total_szr_dur += patient_total_szr_dur
        total_szr_num += patient_total_szr_num

        if patient_total_szr_dur>0:
            total_patient_num_with_szr += 1
            patient_list_with_szr.append(patient_id)
            total_dur_with_szr_labeled += patient_total_dur

print('\n\n\n\nwrst_total_dur = %d seconds, %f hours' % (total_dur, total_dur / 3600))
print('total_dur_labeled = %d seconds, %f hours' % (total_dur_labeled, total_dur_labeled / 3600))
print('total_szr_dur = %d seconds, %f hours' % (total_szr_dur, total_szr_dur / 3600))
print('total_dur_with_szr_labeled = %d seconds, %f hours' % (total_dur_with_szr_labeled, total_dur_with_szr_labeled / 3600))

print('total_patient_num_with_szr = %d ' % total_patient_num_with_szr)
print('total_szr_num = %d ' % total_szr_num)
print('patient_list_with_szr = ', patient_list_with_szr)

# print('total_left_wrst_dur = %d seconds' % total_left_wrst_dur)
# print('total_right_wrst_dur = %d seconds' % total_right_wrst_dur)

# save seizure_len
seizure_len = np.array(seizure_len)
seizure_len_short = seizure_len-40
print('seizure_len_short=',seizure_len_short)
print('seizure_len=',seizure_len)

# seizure_len_short.save
import numpy

np.savetxt("seizure_len_short.csv", seizure_len_short, delimiter=",")
np.savetxt("seizure_len.csv", seizure_len, delimiter=",")

seizure_len_short.tofile('seizure_len_short_1.csv',sep=',',format='%8d')

with open('seizure_len_short.npy', 'wb') as f:
    np.save(f, seizure_len_short)

with open('seizure_len.npy', 'wb') as f:
    np.save(f, seizure_len)