from google.transit import gtfs_realtime_pb2
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import time,os,base64, folium
import urllib.request



def DecryptKey(salt_fname = 'salt.key', encrypted_api_key_fname = 'apikey.key'):
    with open(salt_fname,'rb') as sf:
        salt = sf.read()
    with open(encrypted_api_key_fname,'rb') as af:
        encrypted = af.read()
    password_provided = "password" # This is input in the form of a string
    password = password_provided.encode() # Convert to type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password)) # Can only use kdf once

    f = Fernet(key)
    apikey = f.decrypt(encrypted)
    return apikey

def ConstructFeedURL(line_name,key = DecryptKey()):
    FEED_ID_DICT = {
        '123456S': 1,
        'ACEHS': 26,
        'NQRW': 16,
        'BDFM': 21,
        'L': 2,
        'SIR': 11,
        'G': 31,
        'JZ': 36,
        '7': 51
    }
    url = 'http://datamine.mta.info/mta_esi.php?key='+key.decode()
    if line_name == 'real_time':
        return url
    else:
        assert line_name in FEED_ID_DICT.keys(), 'Usage Error'
        url+='&feed_id='+str(FEED_ID_DICT[line_name])
        return url

def main():
    feed = gtfs_realtime_pb2.FeedMessage()
    url = ConstructFeedURL('ACEHS')
    with urllib.request.urlopen(url) as url_req:
        response = url_req.read()
        feed.ParseFromString(response)
    trips = {}
    for entity in feed.entity:
        tid = entity.vehicle.trip.trip_id
        sid = entity.vehicle.stop_id
        if tid not in trips.keys():
            trips[tid] = []
        trips[tid].append(sid)


if __name__=='__main__': main()
