import pandas as pd
import argparse

# Read CSV file into DataFrame df

parser = argparse.ArgumentParser(description='CSV thinggie')

parser.add_argument('--file', dest='csv_file', required=True,
                    help="Path to the csv file to read.")

df = pd.read_csv(args.csv_file, sep='|')
#print(df)
#for i in df[:10]:
#print(df['timestamp'])

prev_timestamp = 0
for (columnName, timestamp) in df['timestamp'].iteritems():
    try:
        if (int(prev_timestamp) - int(timestamp)) > 100:
            print("We had a problem between timestamp %i and %i" % (int(prev_timestamp), int(timestamp)))
        prev_timestamp = timestamp
    except:
        print("!!!Problem with timestamp: ", timestamp, " Or Prev : ", prev_timestamp)
        break

We had a problem between timestamp 4398045432370 and 212035 #3966643
We had a problem between timestamp 4398045460379 and 949183  #7599557
