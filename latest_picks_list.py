#!/usr/bin/python

# Script to write list of SNCLs with info on latest time the channel
#   was picked as well as latest time the 1) mean amp in counts and 
#   2) 5Hz power exceeded  the 2nd percentile across the PNSN for 
#   that channel code.  Also included are latest values for those
#   two metrics.


import os
import psycopg2
from datetime import datetime, timedelta, timezone 
import pytz
from find_latest_breach import find_latest_breach
from collections import defaultdict
import logging

DB_NAME = os.environ['AQMS_DB']
DB_USER = os.environ['AQMS_USER']
DB_HOST = os.environ['AQMS_HOST1']  # check which is currently secondary
DB_PASSWORD = os.environ['AQMS_PASSWD']

def get_last_picks_for_network(nets, sort_by_sncl=True, file_name='output.txt'):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cur = conn.cursor()

        # Convert the net(s) parameter to handle multiple networks or no network specified
        if nets:
            if isinstance(nets, list):
                nets_list = ', '.join(f"'{net}'" for net in nets)  # Prepare for IN clause
                net_filter = f"a.net IN ({nets_list}) AND "
            else:
                net_filter = f"a.net = '{nets}' AND "
        else:
            net_filter = ""  # No network filter if nets is blank or None

        # Define the query to get all picks from the last year without rounding in SQL
        query = f"""
        SELECT
            a.datetime, ar.orid, ar.delta,
            o.lat AS origin_lat,
            o.lon AS origin_lon,
            o.depth AS origin_depth_km,
            nm.magnitude AS magnitude_l,
            ar.delta AS distance_to_station_km,
            a.net, a.sta, a.location, a.seedchan, a.iphase
        FROM
            arrival a
        JOIN
            assocaro ar ON a.arid = ar.arid
        JOIN
            origin o ON ar.orid = o.orid
        JOIN
            netmag nm ON o.orid = nm.orid
        WHERE
            {net_filter}
            a.datetime >= EXTRACT(EPOCH FROM NOW()) - 31536000
            AND nm.magtype = 'l'
            AND o.subsource = 'Jiggle';
        """

        # Execute the query
        cur.execute(query)
        rows = cur.fetchall()

        # Get current UTC and Pacific time
        utc_time = datetime.now(pytz.UTC)
        pacific_time = utc_time.astimezone(pytz.timezone('US/Pacific'))
        utc_time_str = utc_time.strftime('%Y-%m-%d %H:%M:%S')
        pacific_time_str = pacific_time.strftime('%Y-%m-%d %H:%M:%S')
        timestr = f"{pacific_time_str} local, {utc_time_str} UTC"

        # Convert results into a list of dictionaries for easier processing
        results = []
        for row in rows:
            result = {
                'datetime': int(row[0]),  # Keep as Unix time
                'orid': row[1],
                'delta': round(float(row[2]), 2) if row[2] is not None else None,
                'origin_lat': float(row[3]) if row[3] is not None else None,
                'origin_lon': float(row[4]) if row[4] is not None else None,
                'origin_depth_km': float(row[5]) if row[5] is not None else None,
                'magnitude_l': round(float(row[6]), 2) if row[6] is not None else None,
                'distance_to_station_km': round(float(row[7]), 2) if row[7] is not None else None,
                'net': row[8],
                'sta': row[9],
                'location': row[10] if row[10] not in (None, '', '  ') else '--',
                'seedchan': row[11] if row[11] not in (None, '', ' ') else '--',
                'iphase': row[12],
            }
            results.append(result)

        # Create a dictionary to hold the latest pick for each NSLC
        latest_picks = {}
        for result in results:
            nslc = f"{result['net']}.{result['sta']}.{result['location']}.{result['seedchan']}"
            if nslc not in latest_picks or result['datetime'] > latest_picks[nslc]['datetime']:
                latest_picks[nslc] = result

        # Find latest breach for each nslc for range (SQUAC metricid = 85) and 5sec power (101)
        for nslc in latest_picks:
           # if 'EHZ' in nslc:
                T2 = datetime.now(timezone.utc)
                T1 = T2 - timedelta(days=180)
                breach_time85, breach_value85 = find_latest_breach(nslc, T1, T2, 85, breach_mode='above',verbosity=logging.DEBUG)
                #breach_time101, breach_value101 = find_latest_breach(nslc, T1, T2, 101, breach_mode='above',verbosity=logging.WARNING)
                latest_picks[nslc]['rangebreachdate'] = breach_time85
                latest_picks[nslc]['rangebreachvalue'] = breach_value85
                #latest_picks[nslc]['pow5sbreachdate'] = breach_time101
                #latest_picks[nslc]['pow5sbreachvalue'] = breach_value101

        # Convert latest_picks to a list for sorting
        latest_picks_list = list(latest_picks.items())

        if sort_by_sncl:
            # Group by net.sta and keep ascending order within each group by net.sta
            grouped_by_net_sta = defaultdict(list)
            for nslc, result in latest_picks_list:
                net_sta = f"{result['net']}.{result['sta']}"
                grouped_by_net_sta[net_sta].append((nslc, result))

            # Sort each `net.sta` group by datetime descending within that group
            for net_sta in grouped_by_net_sta:
                grouped_by_net_sta[net_sta].sort(key=lambda x: x[1]['datetime'], reverse=True)

            # Sort groups by `net.sta` in ascending order
            sorted_picks = [(nslc, result) for net_sta in sorted(grouped_by_net_sta.keys()) for nslc, result in grouped_by_net_sta[net_sta]]
        else:
            # Time sorting logic from previous solution
            grouped_by_net_sta = defaultdict(list)
            for nslc, result in latest_picks_list:
                net_sta = f"{result['net']}.{result['sta']}"
                grouped_by_net_sta[net_sta].append((nslc, result))

            for net_sta in grouped_by_net_sta:
                grouped_by_net_sta[net_sta].sort(key=lambda x: x[1]['datetime'], reverse=True)

            sorted_net_sta_groups = sorted(
                grouped_by_net_sta.items(),
                key=lambda x: x[1][0][1]['datetime'],
                reverse=True
            )

            sorted_picks = [(nslc, result) for _, group in sorted_net_sta_groups for nslc, result in group]

        # Write results to file
        daysago7 = (datetime.now() - timedelta(days=7)).timestamp()
        daysago30 = (datetime.now() - timedelta(days=30)).timestamp()
        daysago365 = (datetime.now() - timedelta(weeks=365)).timestamp()
        with open(file_name, 'w') as f:
            f.write(f"Version: {timestr} \n")
            f.write(f"Most recent picks used by Jiggle (either auto or analyst pick):\n")
            for nslc, result in sorted_picks:
                datetime_str = datetime.utcfromtimestamp(result['datetime']).strftime('%Y-%m-%d %H:%M:%S')
                iphase_str = result['iphase'] if result['iphase'] is not None else '--'
                magnitude_str = f"{result['magnitude_l']:>5.2f}" if result['magnitude_l'] is not None else '  N/A'
                origin_lat_str = f"{result['origin_lat']:>6.3f}" if result['origin_lat'] is not None else '   N/A'
                origin_lon_str = f"{result['origin_lon']:>6.3f}" if result['origin_lon'] is not None else '   N/A'
                depth_str = f"{result['origin_depth_km']:>5.2f}" if result['origin_depth_km'] is not None else '   N/A'
                distance_str = f"{result['distance_to_station_km']:>5.1f}" if result['distance_to_station_km'] is not None else '  N/A'
                rangebreachdate_str = (result['rangebreachdate']).strftime('%Y-%m-%d %H:00') if result['rangebreachdate'] is not None else '  N/A'
                rangebreachvalue_str = f"{int(result['rangebreachvalue'])}"  if result['rangebreachvalue'] is not None else '  N/A'
                #pow5sbreachdate_str = (result['pow5sbreachdate']).strftime('%Y-%m-%d %H:00') if result['pow5sbreachdate'] is not None else '  N/A'
                #pow5sbreachvalue_str = f"{int(result['pow5sbreachvalue'])}" if result['pow5sbreachvalue'] is not None else '  N/A'
                count_week, count_month, count_year = 0,0,0
                for res in results:
                    if nslc == f"{res['net']}.{res['sta']}.{res['location']}.{res['seedchan']}":
                        resdate = res['datetime']
                        count_week += 1 if resdate >= daysago7 else 0
                        count_month += 1 if resdate >= daysago30 else 0
                        count_year += 1 if resdate >= daysago365 else 0

                f.write(f"{datetime_str} {iphase_str:>2} {nslc:<16} "
                        f"Mag: {magnitude_str} Origin: ({origin_lat_str}, {origin_lon_str}) "
                        f"Depth: {depth_str} km Dist: {distance_str} km "
                        f" N_picks in last 7dys:{count_week:>3}  30dys:{count_month:>4}  365dys:{count_year:>5}"
                        f" Last breach RangeMin: {rangebreachdate_str} ({rangebreachvalue_str} counts)\n")
                        #f" Power5s breach: {pow5sbreachdate_str} ({pow5sbreachvalue_str} dB)\n")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_last_picks_for_network(nets=[], sort_by_sncl=True, file_name='latest_picks_sncl_sort')
    get_last_picks_for_network(nets=[], sort_by_sncl=False, file_name='latest_picks_time_sort')


