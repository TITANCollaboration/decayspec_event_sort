import requests
import pandas as pd
import json

class online_analyzer_requests:
    def __init__(self):
        self.remote_analyzer_url = "http://titan-decayspec.triumf.ca:9093"
        return

    def web_request(self, payload, weird=False):
        try:
            r = requests.get(self.remote_analyzer_url, params=payload, timeout=2)
            status = 0
        except:
            print("Timeout or other connection issue.")
            mydata_df = pd.DataFrame(data={'0': []})
            status = 1  # Timeout or connection issue
        if weird is True:
            mydata = r.text.replace("'", '"')  # For whatever reason the data coming out of the online analyzer only has single quotes where as it should have double.  I'm doing this instead of fixing the analyzer to make sure the older spectrum viewer will still work.
        else:
            mydata = r.text
        mydata_df = pd.DataFrame(data=json.loads(mydata))

        return mydata_df, status

    def fetch_remote_hist(self, channels):
        payload = {'cmd': 'callspechandler'}
        for index, my_channel in enumerate(channels):
            spectrum = 'spectrum' + str(index)
            payload[spectrum] = my_channel
        print("Payload:", payload)
        mydata_df, status = self.web_request(payload, weird=True)
        return mydata_df, status

    def fetch_remote_2d_hist(self):
        payload = {'cmd': 'getTimeSpec'}
        mydata_df, status = self.web_request(payload)
        return mydata_df, status
