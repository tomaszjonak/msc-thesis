import pandas as pd

avi_data = pd.read_csv('avi_results.csv', header=None, index_col=0, parse_dates=True)
lvm_data = pd.read_csv('lvm_results.csv', header=None, index_col=0, parse_dates=True)

print(avi_data.describe())
print(avi_data.median())
print(lvm_data.describe())
print(lvm_data.median())
