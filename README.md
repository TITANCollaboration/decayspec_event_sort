Python interface to read in TRIUMF MIDAS data format from MDPP16 and GRIF16 ADC's to CSV/HDF5/ROOT files.

Run mds_sort.py , preferably via pypy3

For RAW output:

pypy3 mds_sort.py --midas_file /decayspec_midas/run00297.mid.lz4 --output_file run00297_raw.csv --output_format csv --sort_type raw

For SORTED output:


pypy3 mds_sort.py  --midas_file /decayspec_midas/run00297.mid.lz4 --output_file run00297_sorted.csv --output_format csv --sort_type event --event_length=1900000

#View histogram for single channel from CSV file output of mds_sort, skip after bin 2000

python histos.py --data_file run24285.csv --chan 0 --xmax 2000

#View histogram for three channels from CSV file output of mds_sort, skip after bin 2000 and before min 100

python histos.py --data_file run24285.csv --chan 0 1 3 --xmax 2000 --xmin 100

#View histogram for all channels from CSV file output of mds_sort, bin using 1000 bins

python histos.py --data_file run24285.csv --xmax 2000 --xmin 100 --nbins 1000
