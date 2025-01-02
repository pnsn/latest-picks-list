# latest_picks_list
Generate text file of latest picks for each channel used by PNSN (includes non-PNSN stations like BK, CN).
<br>
<br>
Simple python script that makes query to the AQMS post-processing db and finds the latest pick for each channel as well as counts over the last week, month and year.  The only picks considered are from events that have been Jiggled and (F)inalized or (H)and accepted from the DRP, i.e. a human has looked at it.  Note DRP (H)and accepted events might include a few bogus picks.
<br>
<br>
Results are spit out into two text files sorted by either NET.STA or latest pick time.
<br>
<br>
Updated daily at 6am, noon, 6pm (local, takes 10-15 min to run):
<br>
[latest_picks_sncl_sort](https://seismo.ess.washington.edu/~ahutko/latest_picks_sncl_sort)
<br>
[latest_picks_time_sort](https://seismo.ess.washington.edu/~ahutko/latest_picks_time_sort)
<br>
<br>
What the files look like (roughly 2400 lines/SNCLs long)
<br>
Shown are the latest pick per channel and the event it came from.
<br>
At the end of the line is the N picks for that channel over the last week, month and year.
<br>
<br>
Added at the end is the last time the hourly range (in counts) exceeded a very small number basically indicating when the last real data was sent.  So a dead analog channel with a range of only 5 would not exceed.  "very small number" was determined empirically by data mining all PNSN data in SQUAC for each channel type.  Thresholds for channel type are:
<br>
EN: 20
<br>
HN: 200
<br>
HH: 550
<br>
BH: 650
<br>
EH: 50
<br>
BD:
29000
<br>
This is compared to SQUAC measurements which are behind realtime by 1-3 hrs usually.  Sometimes (very rare) SQUAC can have a hiccup, which could affect this number.

<br>
![Latest_picks_list_output.png](https://github.com/pnsn/latest_picks_list/blob/main/Latest_picks_list_output.png)
<br>
