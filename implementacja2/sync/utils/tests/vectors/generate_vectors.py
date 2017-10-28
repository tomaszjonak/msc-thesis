"""
Script generating test vectors in director in which interpreter was invoked
"""

with open('two_tokens.vector', 'wb') as fd:
    fd.write('first_line\r\n'.encode('utf8'))
    fd.write('second_line\r\n'.encode('utf8'))

with open('instant_eof.vector', 'wb') as fd:
    pass

with open('one_empty_token.vector', 'wb') as fd:
    fd.write('\r\n'.encode('utf8'))

pan_tadzio_name = 'pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt'
bytes_to_write = 1000
with open('pan_tadzio.vector', 'wb') as fd, open(pan_tadzio_name, 'rb') as tfd:
    fd.write('{}\r\n'.format(pan_tadzio_name).encode('utf8'))
    fd.write('{}\r\n'.format(bytes_to_write).encode('utf8'))
    fd.write(tfd.read(bytes_to_write))
    fd.write('\r\n'.encode('utf8'))
