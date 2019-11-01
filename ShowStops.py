import os,sys,folium,re,io
import numpy as np
import pandas as pd
import datetime as dt

from PIL import Image, ImageDraw
from Calculator import *

def InterpolateMissingHours(dft):
    dt_format = '%m/%d/%Y, %H:%M:%S'
    #test_dt_str = '10/22/2019, 03:00:00'
    #test_dt = dt.datetime.strptime(test_dt_str,dt_format)
    interp_df = {}
    for c in dft.columns[1:]:
        interp_df[c] = []
    for s in sorted(dft.STATION.unique()):
        row = dft[dft.STATION==s].iloc[0]
        s_id = row['STATION_ID']
        s_lat = row['STATION_LAT']
        s_lon = row['STATION_LON']
        dates = dft[dft.STATION==s]
        avail_dts = []
        avail_nas = []
        for d in sorted(dates['DATE'].unique()):
            times = dates[dates.DATE==d]
            for t in sorted(times['TIME'].unique()):
                dt_str = '{}, {}'.format(d,t)
                avail_dts.append(dt.datetime.strptime(dt_str,dt_format))
                avail_nas.append(times[times.TIME==t]['NET_ARRIVALS'].item())
        ts = pd.Series(avail_nas, index=avail_dts)
        resampled = ts.resample('H')
        interp = resampled.interpolate()
        for item in interp.iteritems():
            date,time = item[0].strftime('%m/%d/%Y, %H:%M:%S').split(', ')
            interp_df['STATION'].append(s)
            interp_df['STATION_ID'].append(s_id)
            interp_df['STATION_LAT'].append(s_lat)
            interp_df['STATION_LON'].append(s_lon)
            interp_df['DATE'].append(date)
            interp_df['TIME'].append(time)
            interp_df['NET_ARRIVALS'].append(item[1])
    return pd.DataFrame(interp_df)

def FindClosestTimes(dt, avail_dts):
    deltas = []
    for adt in avail_dts:
        #print(adt, dt-adt if dt>adt else adt-dt)
        deltas.append(dt-adt if dt>adt else adt-dt)
    delta_arr = np.array(deltas)
    closest_times = np.array(avail_dts)[delta_arr == delta_arr.min()]
    if len(closest_times) == 2:
        below = closest_times[0]
        above = closest_times[1]
    else:
        min_idx = delta_arr.tolist().index(delta_arr.min())
        min = avail_dts[min_idx]
        if dt < min:
            above = avail_dts[min_idx]
            below = avail_dts[min_idx-1]
        else:
            above = avail_dts[min_idx+1]
            below = avail_dts[min_idx]
    return (below,above)

def CreateMap(dfs,map_dir='./Maps',map_fname='mymap', to_png = True):
    folium_map = folium.Map(location=[40.738, -73.98],
                        zoom_start=13)
    #max_arrivals = dfs['NET_ARRIVALS'].max()
    for idx,row in dfs.iterrows():
        station = row['STATION']
        lat = row['STATION_LAT']
        lon = row['STATION_LON']
        net_arrivals = row['NET_ARRIVALS']
        radius = net_arrivals/100
        #if max_arrivals!=0:
        #    radius = net_arrivals/20
        #else:
        #    radius = 0
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
    # Setting up IO variables for pulling file data
    data_dir = './Data'
    turnstile_fname = 'turnstile_191026.txt'
    stop_fname = 'stops.txt'
    match_fname = 'turnstile_station_to_stop_id.csv'
    full_turnstile_fname = os.path.join(data_dir,turnstile_fname)
    full_stop_fname = os.path.join(data_dir,stop_fname)
    full_match_fname = os.path.join(data_dir,match_fname)

    # Reading data into Pandas DataFrames from csv files
    df_turnstile = pd.read_csv(full_turnstile_fname)
    df_stops = pd.read_csv(full_stop_fname)
    df_match = pd.read_csv(full_match_fname)

    # Calculating net arrivals for each machine in a station and then aggregating by station
    df_turnstile = CalculateNetArrivals(df_turnstile,na_fname = './Data/turnstile_191026_net_arrivals.txt')
    df_stations = CalculateStationNetArrivals(df_turnstile, df_stops, df_match, sna_fname = './Data/station_191026_net_arrivals.txt')

    # Cleaning up the times
    times = ['{:02d}:00:00'.format(i) for i in range(24)]
    df_stations_cleaned_times = df_stations[df_stations.TIME.isin(times)].reset_index(drop=True)

    df_stations_interp = InterpolateMissingHours(df_stations_cleaned_times)

    for d in sorted(df_stations_interp['DATE'].unique()):
        date = df_stations_interp[df_stations_interp['DATE']==d]
        for t in times:
            print('Creating map for {} at {}'.format(d,t))
            df_stations_date_time = GetDateTimeDataFrame(df_stations_interp,d,t)
            CreateMap(df_stations_date_time,map_fname='map_{}_{}'.format(d.replace('/','-'),t))

if __name__=='__main__': main()
