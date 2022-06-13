This project has spawned from just a decoder programer for MIDAS files in the GRIF16 and MDPP16 formats to a more complete analysis suite.  This suite has spawned into 3 different programs all sharing a common library set.

* mds_sort.py - Midas Data System Sorter, this handles taking MIDAS files that were generated via MDPP16 and GRIF16 ADC's and decodes them into any of the following
  * RAW format : This keeps the timestamp and decodes to a format of pulse_heigh, channel, and timestamp, one event per line.  Please check the file's header.
  * Histogram format : This is a Pandas style CSV file with one column per ADC channel with the column representing a histogram of the decoded data
  * Other : There is some functionality for ROOT and HDF5 format's but they are still very experimental

  mds_sort can also handle generating calibration data files and can calibrate a dataset based on the calibration files.  Currently the supported sources for auto-calibration are 60Co and 152Eu.  mds_sort can also group events based on timing windows allowing for correlation of events.

* gammagraph.py - Based on Python Dash this is an online and offline 2d/3d histogram viewer and data analysis suite.  Handles overlaying multiple histograms, calibration data, peak fitting and collaborative peak identification.  Requires installation of Dash 1.21+, loads under Dash 2.0 but not fully tested.  A directory named 'hists' such as ~/decayspec_event_sort/hists must be created in order for uploaded histograms to function.  Histograms can also be directly added to that directory and will then show up in the program.  This is also where .cal files can be placed for calibrated data.

![](https://github.com/TITANCollaboration/decayspec_event_sort/blob/master/images/gamma_graph_linear.png)

* hist_plot.py - Histogram Plotter, primarily designed to generate histogram plots from histogram data, this tool is capable of reading in ROOT files that have a format of pulse_height, chan, flags as well as pandas based CSV histogram format that the mds_sort utility can produce where each column is a histogram per channel separated by '|'.  hist_plot can graph histograms, created zoomed in regions, overlay additional histogram data on top of background histogram data, scale data, smearing data, as well as fit peaks within a region.  Also it can save graphs as png by default and convert root files to the Pandas histogram files.

![](https://github.com/TITANCollaboration/decayspec_event_sort/blob/master/images/neec_with_total_bg_2days_1e7pps_500mA.png)

* hist_utils.py - Histogram Utility program, this handles manipulation of histograms that are in the Pandas CSV format.  It is able to scale histograms, perform gaussian smearing, and sum multiple histograms together.



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
