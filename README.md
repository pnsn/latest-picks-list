# latest_picks_list
Generate text file of latest picks for each channel used by PNSN (includes non-PNSN stations like BK, CN).
<br>
<br>
Simple python script that makes query to the AQMS post-processing db and finds the latest pick for each channel as well as counts over the last week, month and year.
<br>
<br>
Results are spit out into two text files sorted by either NET.STA or latest pick time.
<br>
<br>
Updated daily at 7am and noon (local):
<br>
[latest_picks_sncl_sort](https://seismo.ess.washington.edu/~ahutko/latest_picks_sncl_sort)
<br>
[latest_picks_time_sort](https://seismo.ess.washington.edu/~ahutko/latest_picks_time_sort)
<br>

'''
latest_picks_sncl_sort:
Version: 2024-11-01 15:59:03 local, 2024-11-01 22:59:03 UTC 
Most recent picks used by Jiggle (either auto or analyst pick):
2024-10-31 05:20:53  S BK.CLRV.00.HHN   Mag:  3.05 Origin: (40.552, -120.660) Depth:  3.63 km Dist: 143.7 km N picks in last 7dys:  1  30dys:   5  365dys:   25
2024-10-31 05:20:35  P BK.CLRV.00.HHZ   Mag:  3.05 Origin: (40.552, -120.660) Depth:  3.63 km Dist: 143.7 km N picks in last 7dys:  1  30dys:  11  365dys:   84
2024-10-23 11:40:55  S BK.CLRV.00.HHE   Mag:  2.57 Origin: (41.834, -119.683) Depth: -0.57 km Dist: 118.5 km N picks in last 7dys:  0  30dys:   4  365dys:   32
2024-10-25 11:14:32  S BK.JCC.00.HHZ    Mag:  2.42 Origin: (40.972, -125.464) Depth:  4.62 km Dist: 121.8 km N picks in last 7dys:  0  30dys:   5  365dys:   38
2024-10-31 05:20:56  S BK.MOD.00.HHE    Mag:  3.05 Origin: (40.552, -120.660) Depth:  3.63 km Dist: 153.1 km N picks in last 7dys:  1  30dys:   4  365dys:   46
2024-10-31 05:20:36  P BK.MOD.00.HHZ    Mag:  3.05 Origin: (40.552, -120.660) Depth:  3.63 km Dist: 153.1 km N picks in last 7dys:  1  30dys:  17  365dys:  155
2024-10-23 11:40:36  S BK.MOD.00.HHN    Mag:  2.57 Origin: (41.834, -119.683) Depth: -0.57 km Dist:  51.9 km N picks in last 7dys:  0  30dys:  13  365dys:  104
2023-11-15 23:16:28  S BK.ORV.00.BHZ    Mag:  2.48 Origin: (40.734, -119.622) Depth: -1.51 km Dist: 206.6 km N picks in last 7dys:  0  30dys:   0  365dys:    2
...

latest_picks_time_sort:
Version: 2024-11-01 16:03:24 local, 2024-11-01 23:03:24 UTC 
Most recent picks used by Jiggle (either auto or analyst pick):
2024-11-01 21:27:57  P UW.GNW.--.HHZ    Mag:  1.57 Origin: (47.169, -123.747) Depth: 34.54 km Dist:  82.2 km N picks in last 7dys:  8  30dys:  33  365dys:  421
2024-10-30 12:10:19  S UW.GNW.--.HHN    Mag:  1.14 Origin: (47.645, -122.122) Depth: 15.13 km Dist:  53.5 km N picks in last 7dys:  3  30dys:  17  365dys:  176
2024-10-25 23:47:10  S UW.GNW.--.HHE    Mag:  1.18 Origin: (47.614, -123.561) Depth:  3.43 km Dist:  55.5 km N picks in last 7dys:  1  30dys:   6  365dys:  104
2024-03-08 02:00:03  P UW.GNW.--.ENZ    Mag:  2.39 Origin: (47.627, -123.427) Depth:  4.28 km Dist:  45.6 km N picks in last 7dys:  0  30dys:   0  365dys:    1
2024-11-01 21:27:56  S UW.WYNO.--.HHN   Mag:  1.57 Origin: (47.169, -123.747) Depth: 34.54 km Dist:  31.1 km N picks in last 7dys:  1  30dys:   4  365dys:   47
2024-11-01 21:27:50  P UW.WYNO.--.HHZ   Mag:  1.57 Origin: (47.169, -123.747) Depth: 34.54 km Dist:  31.1 km N picks in last 7dys:  2  30dys:  16  365dys:  195
2024-10-25 04:23:23  S UW.WYNO.--.HHE   Mag:  1.23 Origin: (47.462, -122.905) Depth: 15.74 km Dist:  53.3 km N picks in last 7dys:  0  30dys:   6  365dys:   47
2024-03-08 02:00:08  S UW.WYNO.--.ENN   Mag:  2.39 Origin: (47.627, -123.427) Depth:  4.28 km Dist:  25.6 km N picks in last 7dys:  0  30dys:   0  365dys:    3
...
'''

