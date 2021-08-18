import requests
import pandas as pd


class online_analyzer_requests:
    def __init__(self):
        self.remote_analyzer_url = "http://titan-decayspec.triumf.ca:9093"

        return

    def fetch_remote_hist(self, channels):
        payload = {'cmd': 'callspechandler', 'spectrum1': 'mdpp16_1_Pulse_Height'}
        try:
            r = requests.get(self.remote_analyzer_url, params=payload, timeout=1)
            print(r)
            mydata_df = pd.DataFrame(data={'0': []})
            status = 0
        except:
            print("Timeout or other connection issue.")
            mydata_df = pd.DataFrame(data={'0': []})
            status = 1  # Timeout or connection issue
        return mydata_df, status
