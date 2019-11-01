import os
import numpy as np
import pandas as pd

def CalculateNetArrivals(dft, na_fname=None):
    if na_fname is not None and os.path.exists(na_fname):
        dft_res = pd.read_csv(na_fname)
    else:
        delta_entries = []
        delta_exits = []
        prev_scp = dft['SCP'][0]
        for idx,row in dft.iterrows():
            curr_scp = row['SCP']
            if idx==0 or curr_scp != prev_scp:
                delta_entries.append(0)
                delta_exits.append(0)
            else:
                delta_entries.append(row['ENTRIES']-prev_entries)
                delta_exits.append(row['EXITS']-prev_exits)
            prev_entries = row['ENTRIES']
            prev_exits = row['EXITS']
            prev_scp = curr_scp

        dft['DELTA_ENTRIES'] = delta_entries
        dft['DELTA_EXITS'] = delta_exits
        dft['NET_ARRIVALS'] = np.array(delta_entries)-np.array(delta_exits)
        dft_res = dft
        if na_fname is not None:
            dft.to_csv(na_fname)
    return dft_res

def CalculateStationNetArrivals(dft,dfs,dfm,sna_fname = None):
    if sna_fname is not None and os.path.exists(sna_fname):
        dfsn = pd.read_csv(sna_fname)
    else:
        stations = sorted(dft['STATION'].unique())
        data = {
            'STATION':[],
            'STATION_ID':[],
            'STATION_LAT':[],
            'STATION_LON':[],
            'DATE':[],
            'TIME':[],
            'NET_ARRIVALS':[]
        }

        for s in stations:
            sim_st = dft[dft['STATION'] == s]
            st_id = dfm[dfm['STATION']==s]['stop_id']
            if len(st_id)>0:
                st_id = st_id[st_id.index[0]]
                st_lat = dfs[dfs['stop_id']==st_id]['stop_lat']
                st_lat = st_lat[st_lat.index[0]]
                st_lon = dfs[dfs['stop_id']==st_id]['stop_lon']
                st_lon = st_lon[st_lon.index[0]]
                for d in sim_st['DATE'].unique():
                    sim_st_d = sim_st[sim_st['DATE'] == d]
                    for t in sim_st_d['TIME'].unique():
                        sim_st_d_t = sim_st_d[sim_st_d['TIME'] == t]
                        if not sim_st_d_t.empty:
                            data['STATION'].append(s)
                            data['STATION_ID'].append(st_id)
                            data['STATION_LAT'].append(st_lat)
                            data['STATION_LON'].append(st_lon)
                            data['DATE'].append(d)
                            data['TIME'].append(t)
                            data['NET_ARRIVALS'].append(sim_st_d_t['NET_ARRIVALS'].sum())
        dfsn = pd.DataFrame(data)
        if sna_fname is not None:
            dfsn.to_csv(sna_fname)
    return dfsn

def GetDateTimeDataFrame(dfs,date,time):
    dfs_d = dfs[dfs['DATE']==date]
    dfs_d_t = dfs_d[dfs_d['TIME']==time]
    return dfs_d_t
