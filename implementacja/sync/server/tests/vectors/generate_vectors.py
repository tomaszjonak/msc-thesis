import datetime as dt

tadeusz_path = 'pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt'
tadeusz_test_size = 1000

# 'M%y%m%d/M%y%m%d-%H%M%S'
base_date = dt.datetime.strptime('M000101-000000', 'M%y%m%d-%H%M%S')
def get_name(case, file):
    return (base_date + dt.timedelta(days=case, seconds=file)).strftime('M%y%m%d/M%y%m%d-%H%M%S')

# 'M%y%m%d/M%y%m%d-%H%M%S'
case_0_file_1_name = get_name(0, 0)
with open('one_file.vector', 'wb') as dest_fd:
    dest_fd.write('{}\r\n'.format(case_0_file_1_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size))
    dest_fd.write('\r\n'.encode('utf8'))

case_1_file_1_name = get_name(1, 0)
case_1_file_2_name = get_name(1, 1)
with open('two_equall_length.vector', 'wb') as dest_fd:
    dest_fd.write('{}\r\n'.format(case_1_file_1_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size))
    dest_fd.write('\r\n'.encode('utf8'))
    dest_fd.write('{}\r\n'.format(case_1_file_2_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size))
    dest_fd.write('\r\n'.encode('utf8'))

case_2_file_1_name = get_name(2, 0)
case_2_file_2_name = get_name(2, 1)
with open('two_increasing_length.vector', 'wb') as dest_fd:
    dest_fd.write('{}\r\n'.format(case_2_file_1_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size))
    dest_fd.write('\r\n'.encode('utf8'))

    dest_fd.write('{}\r\n'.format(case_2_file_2_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size*2).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size*2))
    dest_fd.write('\r\n'.encode('utf8'))

case_3_file_1_name = get_name(3, 0)
case_3_file_2_name = get_name(3, 1)
with open('two_decreasing_length.vector', 'wb') as dest_fd:
    dest_fd.write('{}\r\n'.format(case_3_file_1_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size * 2).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size * 2))
    dest_fd.write('\r\n'.encode('utf8'))

    dest_fd.write('{}\r\n'.format(case_3_file_2_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(tadeusz_test_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(tadeusz_test_size))
    dest_fd.write('\r\n'.encode('utf8'))


small_size = 100
case_4_file_2_name = get_name(4, 1)
case_4_file_1_name = get_name(4, 0)
with open('two_no_cache_update.vector', 'wb') as dest_fd:
    dest_fd.write('{}\r\n'.format(case_4_file_2_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(small_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(small_size))
    dest_fd.write('\r\n'.encode('utf8'))

    dest_fd.write('{}\r\n'.format(case_4_file_1_name).encode('utf8'))
    dest_fd.write('{}\r\n'.format(small_size).encode('utf8'))
    with open(tadeusz_path, 'rb') as source_fd:
        dest_fd.write(source_fd.read(small_size))
    dest_fd.write('\r\n'.encode('utf8'))
