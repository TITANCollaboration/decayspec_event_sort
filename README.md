Python interface to read in TRIUMF MIDAS data format from MDPP16 and GRIF16 ADC's to CSV/HDF5/ROOT files.

Run mds_sort.py , preferably via pypy3

For RAW output:

pypy3 mds_sort.py --midas_file /decayspec_midas/run00297.mid.lz4 --output_file run00297_raw.csv --output_format csv --sort_type raw

For SORTED output:


pypy3 mds_sort.py  --midas_file /decayspec_midas/run00297.mid.lz4 --output_file run00297_sorted.csv --output_format csv --sort_type event --event_length=1900000
