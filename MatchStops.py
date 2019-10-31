import pandas as pd
from Levenshtein import ratio

def MatchStops(turnstile_fname = './Data/turnstile_191026.txt', stops_fname = './Data/stops.txt', output_fname = 'test.csv'):
    dft = pd.read_csv(turnstile_fname)
    dfs = pd.read_csv(stops_fname)
    turnstile_stop_names = []
    stop_stop_names = []
    matches = []
    for x in sorted(dft['STATION'].unique()):
        stop_name = x
        lower_stop_name = x.lower()
        turnstile_stop_names.append((lower_stop_name,stop_name))
    for x in sorted(dfs['stop_name'].unique()):
        stop_id = dfs['stop_id'][dfs['stop_name']==x]
        stop_stop_names.append((x.lower(),stop_id[stop_id.index[0]]))
    for turn in turnstile_stop_names:
        ratio_list = []
        for stop in stop_stop_names:
            ratio_list.append((stop[0],stop[1],turn[0],turn[1],ratio(turn[0],stop[0])))
        best_match = sorted(ratio_list,key=lambda x: x[-1])[-1]
        if best_match[-1] < 0.7:
            print('{}-->{}'.format(turn[1],best_match))
        else:
            matches.append((turn[1],best_match[1]))
    pd.DataFrame(matches,columns=['STATION','stop_id']).to_csv(output_fname)

if __name__=='__main__': MatchStops()
