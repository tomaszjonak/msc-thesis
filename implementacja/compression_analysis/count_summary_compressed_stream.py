import pandas as pd
import numpy as np
import itertools


def main():
    lvm_df = pd.read_csv('lvm_results.csv')
    avi_df = pd.read_csv('avi_results.csv')
    h264_df = pd.read_csv('x264_params.csv')

    # df.loc[df['column_name'] == some_value]
    avi_df['x264'] = h264_df.loc[h264_df['preset'] == 'veryslow']['compressed_size'].reset_index()

    # Take size in kilobytes
    original_dataset_size = (lvm_df['original_size'].sum() + avi_df['original_size'].sum()) / 1000
    print('{} Kb'.format(original_dataset_size))

    lvm_methods = ['lzma', 'bz2', 'zlib']
    avi_methods = ['lzma', 'bz2', 'zlib', 'x264']

    def calculate_compression(x):
        lvm_method = x.index
        avi_method = x.name
        lvm_size = lvm_df[lvm_method].sum() / 1000
        avi_size = avi_df[avi_method].sum() / 1000
        return (avi_size + lvm_size) / original_dataset_size * 100

    result_df = pd.DataFrame(np.nan, index=lvm_methods,columns=avi_methods).apply(calculate_compression)
    result_df.to_csv('compression_method_matrix.csv', float_format='%.2f')
    print(result_df)
    # for lvm_m, avi_m in itertools.product(lvm_methods, avi_methods):



    # print('Kompresja lvm z presetem slow: {0:.2f} %'.format(compression_ratio))


if __name__ == '__main__':
    main()
