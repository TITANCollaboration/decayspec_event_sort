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
        if (prev_timestamp - timestamp) > 100:
            print("We had a problem between timestamp %i and %i" % (prev_timestamp, timestamp))
        prev_timestamp = timestamp
    except:
        print("!!!Problem with timestamp: ", timestamp, " Or Prev : ", prev_timestamp)
        break
