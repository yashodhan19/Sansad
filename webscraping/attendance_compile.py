import pandas as pd
from os import listdir
from os.path import isfile, join
import os

mypath = os.path.join(os.getcwd(), "LOKSABHA_ATTENDANCE")
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

csv_all = pd.DataFrame(columns= ['Unnamed: 0', 'divNo', 'MemberName', 'AttendanceStatus', 'ls_session', 'ls_date'])
for i in onlyfiles:
    csv_new = pd.read_csv(mypath + '\\' +i, sep='|')
    csv_all = pd.concat([csv_all, csv_new], axis=0)

attend = pd.DataFrame({'AttendanceStatus':['NR','NS','S'], 'Attendance':[1,0,1]})

csv_all = csv_all.merge(attend, how='left', on='AttendanceStatus')

attendance_mean = csv_all.groupby('MemberName', as_index=False).mean()
attendance_count = csv_all.groupby('MemberName', as_index=False).count()

merge = attendance_mean.merge(attendance_count, how='left', on='MemberName')
merge.to_csv('merge.csv')
#
# print(csv_new.shape)
# print(len(onlyfiles))
# print(csv_all.shape)
# #print(onlyfiles)
# attend = {'NR': 1, 'NS': 0, 'S': 1}
# test_file = pd.read_csv(mypath + '\\' + onlyfiles[0], sep='|')
# print(test_file.columns)
# print(test_file['AttendanceStatus'].unique())


