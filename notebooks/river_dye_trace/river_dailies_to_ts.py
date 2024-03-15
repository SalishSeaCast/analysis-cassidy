import numpy as np
import xarray as xr
import os
import re
import sys
import pandas as pd
from datetime import datetime
import salishsea_tools.river_202108 as rivers  # if you want to find river inputs for a different (future?) version of rivers, you'll have to change this the files_between_dates fn!
import salishsea_tools.river_201702 as rivers2

rlist_dict = {'test': [['fraser', 'Fraser'], ['skagit', 'Skagit1']],
              'fraser': [['fraser', 'Fraser']],
              'Cassidy': [['fraser', 'Nooksack'], ['skagit', 'Skagit1'], ['skagit', 'SnohomishAllenQuilceda'], ['puget', 'NisquallyMcAllister'], \
                          ['jdf', 'Elwha'], ['evi_s', 'Cowichan1'], ['evi_s', 'Nanaimo1'], ['evi_s', 'Puntledge'], ['evi_n', 'SalmonSayward'], ['bute', 'Homathko'], \
                            ['howe', 'Squamish']]}

def main(start_str, end_str, source_directory, save_name, rlist_call, river_ver):
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 7:
        print("Usage: python river_dailies_to_ts.py yyyymmdd_start yyyymmdd_end source_dir save_name river_list river_ver\
              \n files save as 'river_dailies_to_ts_save_name_yyyymmdd_start_yyyymmdd_end.csv'\
              \n river forcings are in source_dir='/results/forcing/rivers/'")
        

    def files_between_dates(start_date, end_date, directory, river_ver):
        files = []
        file_dates = []

        if (river_ver == '202108'):
            date_pattern = r'R202108Dailies_y(\d{4})m(\d{2})d(\d{2})'  # regex pattern to specifically match the 202108Dailies
        if (river_ver == '201702'):
            date_pattern = r'R201702DFraCElse_y(\d{4})m(\d{2})d(\d{2})'  # regex pattern to specifically match the R201702DFraCElse
        
        for filename in sorted(os.listdir(directory)):
            match = re.search(date_pattern, filename)
            if match:
                year, month, day = map(int, match.groups())
                file_date = datetime(year, month, day).date()
                if start_date <= file_date <= end_date:
                    files.append(filename)
                    file_dates.append(file_date.strftime('%m-%d-%Y'))
        
        return files, file_dates
    

    # the entire set of rivers and their w_shed/r_call pairs is located in /ocean/cdonaldson/MEOPAR/tools/SalishSeaTools/salishsea_tools/river_202108.py
    # this fn looks up and returns the river input coordinates and widths
    def river_bounds(river, river_ver):

        if (river_ver == '202108'):
            import salishsea_tools.river_202108 as rivers  # match locations for the 202108Dailies
        if (river_ver == '201702'):
            import salishsea_tools.river_201702 as rivers  # match locations for the R201702DFraCElse

        w_shed = river[0]
        r_call = river[1]

        y = rivers.prop_dict[w_shed][r_call]['i']  # model grid Y-axis
        x = rivers.prop_dict[w_shed][r_call]['j']  # model grid X-axis
        dy = rivers.prop_dict[w_shed][r_call]['di']  # the number of boxes in Y
        dx = rivers.prop_dict[w_shed][r_call]['dj']  # the number of boxes in X

        return y, dy, x, dx
    # when selecting from the big array, do it like [y:y+dy, x:x+dx]
    # np.array([[1, 2, 3], [4, 5, 6], [7, 8 ,9]])[0:1, 2:3] = array([[3]]), specifies the row then the column


    def files_to_timeseries(directory, file_names, rivers, river_ver):

        num_rows = len(file_names)
        num_cols = len(rivers)

        result = np.zeros((num_rows, num_cols), dtype=float)  # allocate memory based on # days and # rivers

        row_idx = 0
        col_idx = 0

        for file in file_names:
            fname = directory + file
            ds = xr.open_dataset(fname)
            array = ds['rorunoff'].values[0, :, :]  # og shape is (1, 898, 398)

            for river in rivers:
                y, dy, x, dx = river_bounds(river, river_ver)
                result[row_idx, col_idx] = array[y:y+dy, x:x+dx].sum()  # take the sum in the box, slices are not inclusive
                col_idx += 1
            
            ds.close()  # close the dataset for this day before opening the next one

            col_idx = 0  # reset the river idx to loop again
            row_idx += 1  # add one to the file idx

        return result
    

    start_date = datetime.strptime(start_str, '%Y%m%d').date()
    end_date = datetime.strptime(end_str, '%Y%m%d').date()

    rivers_list = rlist_dict[rlist_call]

    file_names, file_dates = files_between_dates(start_date, end_date, source_directory, river_ver)
    result = files_to_timeseries(source_directory, file_names, rivers_list, river_ver)

    data_dict = {}
    for i in np.arange(len(rivers_list)):
        river_name = rivers_list[i][1] + ' [kg/m2/s]'
        data_dict[river_name] = result[:,i]
    df_data = pd.DataFrame(data_dict)

    metas = {'filename':file_names, 'date':file_dates}
    df_metas = pd.DataFrame(metas)

    df_all = pd.concat([df_metas, df_data], axis=1)

    file_to_save_name = 'river_dailies_to_ts_{}_{}_{}.csv'.format(save_name, start_str, end_str)
    df_all.to_csv(file_to_save_name)

    print('File saved as {}'.format(file_to_save_name))

if __name__ == "__main__":
    start_str = sys.argv[1]
    end_str = sys.argv[2]
    source_directory = sys.argv[3]
    save_name = sys.argv[4]
    rlist_call = sys.argv[5]
    river_ver = sys.argv[6]
    main(start_str, end_str, source_directory, save_name, rlist_call, river_ver)