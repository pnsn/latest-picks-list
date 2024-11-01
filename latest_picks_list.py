#!/home/seis/miniconda3/envs/squac/bin/python

import os
import psycopg2
from datetime import datetime
import pytz

DB_NAME = os.environ['AQMS_DB']
DB_USER = os.environ['AQMS_USER']
DB_HOST = os.environ['AQMS_HOST1']  # check which is currently secondary
DB_PASSWORD = os.environ['AQMS_PASSWD']

import psycopg2
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

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

                count_week = sum(1 for res in results if f"{res['net']}.{res['sta']}.{res['location']}.{res['seedchan']}" == nslc and res['datetime'] >= (datetime.now() - timedelta(weeks=1)).timestamp())
                count_month = sum(1 for res in results if f"{res['net']}.{res['sta']}.{res['location']}.{res['seedchan']}" == nslc and res['datetime'] >= (datetime.now() - timedelta(days=30)).timestamp())
                count_year = sum(1 for res in results if f"{res['net']}.{res['sta']}.{res['location']}.{res['seedchan']}" == nslc and res['datetime'] >= (datetime.now() - timedelta(days=365)).timestamp())

                f.write(f"{datetime_str} {iphase_str:>2} {nslc:<16} "
                        f"Mag: {magnitude_str} Origin: ({origin_lat_str}, {origin_lon_str}) "
                        f"Depth: {depth_str} km Dist: {distance_str} km "
                        f"N picks in last 7dys:{count_week:>3}  30dys:{count_month:>4}  365dys:{count_year:>5}\n")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_last_picks_for_network(nets=[], sort_by_sncl=True, file_name='latest_picks_sncl_sort')
    get_last_picks_for_network(nets=[], sort_by_sncl=False, file_name='latest_picks_time_sort')



