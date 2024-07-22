import numpy as np
import pandas as pd

import matplotlib.pyplot as plt


def parse_dat(filename):

    with open(filename, 'r') as fid:
        fid.readline()

        var_line = fid.readline()
        var_line = var_line.replace('VARIABLES=', '')
        var_line = var_line.replace('"\n', '')
        varnames = [ var.strip('"')for var in var_line.split(' ')]

        fid.readline()

        return pd.read_csv(fid, sep='  ', names=varnames, engine='python')


    
def plot_residuals(df):

    for col in df.columns:
        if 'R_' in col:

            plt.figure()
            plt.plot(df['Iteration'], df[col])
            
            plt.yscale('log')
            plt.xlabel('Iteration')
            plt.ylabel('Value')
            plt.title(col)

    plt.show()







 





if __name__ == '__main__':

    data = parse_dat('Fin_Can_Stubby_trisurf_v1p2_FINAL_hist.dat')

    plot_residuals(data)













