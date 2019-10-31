import os,sys,folium,re,io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

def Interpolate(df1,df2,x):
    df = df1*(1-x)+df2*x
    return df.replace(np.nan,0)

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

def CreateMap(dfs,map_dir='./Maps',map_fname='mymap', to_png = True):
    folium_map = folium.Map(location=[40.738, -73.98],
                        zoom_start=13)
    max_arrivals = dfs['NET_ARRIVALS'].max()
    print(max_arrivals)
    for idx,row in dfs.iterrows():
        station = row['STATION']
        lat = row['STATION_LAT']
        lon = row['STATION_LON']
        net_arrivals = row['NET_ARRIVALS']
        if max_arrivals!=0:
            radius = net_arrivals/(max_arrivals/20)
        else:
            radius = 0
        if net_arrivals>0:
            color="#E37222" # tangerine
        else:
            color="#0A8A9F" # teal
        popup_text = "{}<br>net arrivals: {}"
        popup_text = popup_text.format(station,net_arrivals)
        marker = folium.CircleMarker(location=[lat,lon],radius=radius,color=color,fill=True,popup = popup_text)
        marker.add_to(folium_map)
    if not os.path.exists(map_dir):
        os.makedirs(map_dir)
    if to_png:
        png = folium_map._to_png()
        image = Image.open(io.BytesIO(png))
        image.save(os.path.join(map_dir,map_fname+'.png'),'PNG')
    else:
        folium_map.save(os.path.join(map_dir,map_fname+'.html'))

def main():
    data_dir = './Data'
    turnstile_fname = 'turnstile_191026.txt'
    stop_fname = 'stops.txt'
    match_fname = 'turnstile_station_to_stop_id.csv'

    full_turnstile_fname = os.path.join(data_dir,turnstile_fname)
    full_stop_fname = os.path.join(data_dir,stop_fname)
    full_match_fname = os.path.join(data_dir,match_fname)

    df_turnstile = pd.read_csv(full_turnstile_fname)
    df_stops = pd.read_csv(full_stop_fname)
    df_match = pd.read_csv(full_match_fname)

    df_turnstile = CalculateNetArrivals(df_turnstile,na_fname = './Data/turnstile_191026_net_arrivals.txt')
    df_stations = CalculateStationNetArrivals(df_turnstile, df_stops, df_match, sna_fname = './Data/station_191026_net_arrivals.txt')
    d = '10/19/2019'
    t = '04:00:00'
    df_stations_date_time_4 = GetDateTimeDataFrame(df_stations,d,t)
    t = '08:00:00'
    df_stations_date_time_8 = GetDateTimeDataFrame(df_stations,d,t)
    print(df_stations_date_time_4['NET_ARRIVALS'].head())
    print(df_stations_date_time_8['NET_ARRIVALS'].head())
    print(Interpolate(df_stations_date_time_4['NET_ARRIVALS'].reset_index(drop=True),df_stations_date_time_8['NET_ARRIVALS'].reset_index(drop=True),0.5))

    """
    for d in sorted(df_stations['DATE'].unique()):
        for t in ['00:00:00','04:00:00','08:00:00','12:00:00','16:00:00','20:00:00']:
            print('Creating map for {} at {}'.format(d,t))
            df_stations_date_time = GetDateTimeDataFrame(df_stations,d,t)
            CreateMap(df_stations_date_time,map_fname='map_{}_{}'.format(d.replace('/','-'),t))
    """

if __name__=='__main__': main()
