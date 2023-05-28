# reduce size of storage: https://www.sohu.com/a/342828504_120123190

from collections import namedtuple


'''
szr_label: szr (1), control (0), not valid (-1)
base_type: focal(0), generalised(1), unknown(2)
motor_type: motor, non_motor, unclassified, subclinical
focal_aware_type: aware, impaired_aware, unclassified, btc
sub_type: varies according base_type and motor_type
'''
# Szr_semiology = namedtuple('Szr_semiology',['szr_label','base_type','motor_type','focal_aware_type','sub_type'])
#
# szr_semiology = Szr_semiology(szr_label='szr', base_type='focal', motor_type='motor', focal_aware_type='aware', sub_type='xxx')
#
#
# szr_semiologys = []
# for idx in range(5):
#     szr_semiology = szr_semiology._replace(szr_label='not valid')
#     szr_semiologys.append(szr_semiology)
# print(szr_semiologys)



import numpy as np
Point = np.dtype([('x', np.int32), ('y', np.int32), ('z', np.int32)])
points = np.zeros(10, dtype=Point)


Szr_semiology = np.dtype([('szr_label','S20'),('base_type','S20'),('motor_type','S20'),('focal_aware_type','S20'),('sub_type','S20')])
szr_semiologys = np.empty(10, dtype=Szr_semiology)
szr_semiologys[0:10] = ('abc', '21', '50','qwew','erqwe')



student = np.dtype([('name','S20'), ('age', 'i1'), ('marks', 'f4')])

# a = np.array([('abc', 21, 50),('xyz', 18, 75)], dtype = student)

a = np.empty(100,dtype = student)

a[0:10]=('abc', 21, 50)

a[0]['name'] = 'edc'

print(a)

szr_semiology = np.dtype()

aaa=1