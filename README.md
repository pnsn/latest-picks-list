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
Updated daily at 7am and noon (local):
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

![latest_picks_list](https://github.com/user-attachments/assets/31057ab0-287c-459b-aff5-ae97086939e6)
