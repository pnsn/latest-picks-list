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
Updated daily at 6am and noon (local, takes 10-15 min to run):
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
At the end of the line is the N picks for that channel over the last week, month and year
<br>
and the last time the range (in counts) exceeded "really low", i.e. last time real data was sent.
<br>
"really low" was empirically determined for each channel type by data mining across all of PNSN.
<br>
This is determined by pulling measurements from SQUAC which is usually pretty reliable, but very rarely craps out.
<br>
![latest_picks_screengrab](https://github.com/user-attachments/assets/ee69feb2-d7e4-452c-bcb2-96b9ccab44ff)
