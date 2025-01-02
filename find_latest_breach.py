import logging
import os
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import requests
from squacapi_client.pnsn_utilities import get_client
from squacapi_client.models import *

###############################################################################
# Global Configuration
###############################################################################

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

USER = os.environ["SQUACAPI_USER"]
PASSWORD = os.environ["SQUACAPI_PASSWD"]
HOST = "https://squacapi.pnsn.org"
squac_client = get_client(USER, PASSWORD)

# Load channel map from file (e.g., "squac_channel_map.txt").
url = "https://seismo.ess.washington.edu/~ahutko/ShakeAlert_Chanfiles/squac_channel_map.txt"
response = requests.get(url)
lines = response.text.splitlines()
_channel_map = {}
try:
    for line in lines:
        sncl, chid = line.split()[0], line.split()[1]
        _channel_map[sncl] = chid
except Exception as e:
    logger.error(f"Error reading channel map file: {e}")
    raise

# Default thresholds for known metrics:
#   - metric_id = 85 => “hourly range”
#   - metric_id = 101 => “5s power”
chantypes = ["EN", "HN", "HH", "BH", "EH", "BD", "DH"]
thresh_range = [20, 200, 550, 650, 50, 29000, 200]  # For metric_id=85
thresh_5s_power = [-122.6, -123.0, -130.3, -129.8, -150.0, -39.0, -130.0]  # For metric_id=101

DEFAULT_THRESHDICT = {
    85: dict(zip(chantypes, thresh_range)),
    101: dict(zip(chantypes, thresh_5s_power)),
}


###############################################################################
# Main Function: find_latest_breach
###############################################################################

def find_latest_breach(
    sncl,
    T1,
    T2=None,
    metric_id=None,
    user_threshold_dict=None,
    channel_map=None,
    verbosity=logging.WARNING,
    breach_mode="above"
):
    """
    Finds the latest time/value breach within [T1, T2] for a single SNCL,
    using a hierarchical search: hour → day → week → month. If a breach
    is found at a coarse granularity (e.g. monthly), it refines by descending
    to weekly → daily → hourly.

    By default, a "breach" means value > threshold ("above"). You can change
    this to "below" to indicate you want to detect values that fall below
    threshold, in which case the code will look at meas.min or meas.value
    instead of meas.max.

    Parameters
    ----------
    sncl : str
        The SNCL to search (e.g. "UW.TKEY.--.ENZ").

    T1 : datetime
        The start of the search window. Any discovered breach time < T1 is
        excluded from the result.

    T2 : datetime, optional
        The end of the search window. Defaults to current UTC if None.

    metric_id : int, optional
        SQUAC metric ID. If 85 or 101, we use built-in defaults unless the user
        provides user_threshold_dict.

    user_threshold_dict : dict, optional
        A dict mapping channel types ("EN", "HH", etc.) to float thresholds.
        If None and metric_id is 85 or 101, built-in defaults are used.

    channel_map : dict, optional
        Maps SNCL strings to channel IDs. If None, uses the globally loaded
        _channel_map from file.

    verbosity : int
        Logging level (e.g., logging.DEBUG, logging.INFO). Defaults to WARNING.
        verbosity=logging.DEBUG (or =10) will show each database query parameters.

    breach_mode : str, optional
        Either "above" (default) or "below". If "above", a breach is val > threshold.
        If "below", a breach is val < threshold, using .min if available.

    Returns
    -------
    (breach_time, breach_value) : (datetime or None, float or None)
        The latest breach time in [T1, T2] and the breach value, or (None, None)
        if no breach is found or if no data is returned.

    Notes
    -----
    - Hourly data is near real-time minus 1-3 hours.
    - Daily archives represent full days (00:00 - 23:59:59).
    - Weekly archives can begin any day/hour for a given SNCL+metric, and SQUAC
      does not return a weekly block if its starttime < the query’s starttime.
      We may thus query from T1-7 days to include that partial block if it
      crosses T1.
    - Monthly archives yield one measurement covering the entire month.
    - Archives may be delayed, so you can get no data if you query too soon.
    - The function attempts to find “recent” breaches near T2 with hourly data
      first, then expands backward if none is found.
    """
    log = logging.getLogger(__name__)
    log.setLevel(verbosity)

    # Default T2 to now (UTC) if not provided
    if T2 is None:
        T2 = datetime.now(timezone.utc)

    # If no explicit channel map is provided, use the global _channel_map
    if channel_map is None:
        channel_map = _channel_map

    # If the user didn’t provide thresholds, but metric_id is recognized (85,101),
    # use the built-in defaults.
    if user_threshold_dict is None and metric_id in (85, 101):
        threshold_dict = DEFAULT_THRESHDICT[metric_id]
    else:
        threshold_dict = user_threshold_dict

    # Basic sanity check
    if T1 >= T2:
        log.warning(f"T1 ({T1}) >= T2 ({T2}); no breach possible.")
        return None, None

    if threshold_dict is None:
        log.warning(f"No threshold dict for metric_id={metric_id}. No breach can be determined.")
        return None, None

    # If the time range is <1 day, just do an hourly search once.
    if (T2 - T1) < timedelta(days=1):
        log.info("Time range < 1 day; searching hourly only.")
        return _search_granularity(
            sncl, T1, T2, metric_id, threshold_dict, channel_map, log, "hour", T1, breach_mode
        )

    # 1. Quick Hourly Check near T2
    if T2.hour > 2:
        hour_start = T2.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        hour_start = T2.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    breach_time, breach_value = _search_granularity(
        sncl, hour_start, T2, metric_id, threshold_dict, channel_map, log, "hour", T1, breach_mode
    )
    if breach_time:
        return breach_time, breach_value

    # 2. Daily Check (last 7 days)
    day_start = T2.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    if day_start < T1:
        day_start = T1

    breach_time, breach_value = _search_granularity(
        sncl, day_start, T2, metric_id, threshold_dict, channel_map, log, "day", T1, breach_mode
    )
    if breach_time:
        # Refine to hour within that day
        dstart, dend = _get_granularity_bounds(breach_time, "day", T1, T2)
        b2, v2 = _search_granularity(
            sncl, dstart, dend, metric_id, threshold_dict, channel_map, log, "hour", T1, breach_mode
        )
        if b2:
            return b2, v2

    # 3. Weekly (up to 6 weeks)
    weeks_to_search = min(6, (T2 - T1).days // 7)

    expanded_weekly_start = T1 - timedelta(days=7)  # may catch partial block
    if expanded_weekly_start < datetime(1970, 1, 1, tzinfo=timezone.utc):
        expanded_weekly_start = datetime(1970, 1, 1, tzinfo=timezone.utc)

    week_end = T2
    for _ in range(weeks_to_search):
        week_start = max(expanded_weekly_start, week_end - timedelta(weeks=1))
        breach_time, breach_value = _search_granularity(
            sncl, week_start, week_end, metric_id, threshold_dict, channel_map, log, "week", T1, breach_mode
        )
        if breach_time:
            # refine to daily
            wstart, wend = _get_granularity_bounds(breach_time, "week", T1, T2)
            b2, v2 = _search_granularity(
                sncl, wstart, wend, metric_id, threshold_dict, channel_map, log, "day", T1, breach_mode
            )
            if b2:
                # refine to hour
                dstart, dend = _get_granularity_bounds(b2, "day", T1, T2)
                b3, v3 = _search_granularity(
                    sncl, dstart, dend, metric_id, threshold_dict, channel_map, log, "hour", T1, breach_mode
                )
                if b3:
                    return b3, v3
        week_end = week_start

    # 4. Monthly
    mstart, mend = _get_granularity_bounds(T1, "month", T1, T2)
    b1, v1 = _search_granularity(
        sncl, mstart, T2, metric_id, threshold_dict, channel_map, log, "month", T1, breach_mode
    )
    if b1:
        # The monthly measurement indicates a breach somewhere in that month.
        # To refine further, we do weekly again but expand T1 by 7 days.
        wstart = b1 - timedelta(days=7)
        wend = b1 + relativedelta(months=1)
        if wstart < datetime(1970, 1, 1, tzinfo=timezone.utc):
            wstart = datetime(1970, 1, 1, tzinfo=timezone.utc)

        b2, v2 = _search_granularity(
            sncl, wstart, wend, metric_id, threshold_dict, channel_map, log, "week", T1, breach_mode
        )
        if b2:
            # refine to daily
            wstart, wend = _get_granularity_bounds(b2, "week", T1, T2)
            b3, v3 = _search_granularity(
                sncl, wstart, wend, metric_id, threshold_dict, channel_map, log, "day", T1, breach_mode
            )
            if b3:
                # refine to hour
                dstart, dend = _get_granularity_bounds(b3, "day", T1, T2)
                b4, v4 = _search_granularity(
                    sncl, dstart, dend, metric_id, threshold_dict, channel_map, log, "hour", T1, breach_mode
                )
                if b4:
                    return b4, v4

    log.info(f"No breach found for SNCL {sncl} in [{T1}–{T2}].")
    return None, None


###############################################################################
# Internal Helper: _search_granularity
###############################################################################

def _search_granularity(
    sncl,
    starttime,
    endtime,
    metric_id,
    threshold_dict,
    channel_map,
    log,
    granularity,
    T1,
    breach_mode="above"
):
    """
    Queries the SQUAC API for measurements at a given granularity
    ('hour', 'day', 'week', or 'month') within [starttime, endtime].
    Returns (latest_breach_time, latest_breach_value), or (None, None)
    if no data or no breaches are found.

    Any discovered breach time < T1 is ignored.

    If breach_mode == "above", we compare max or value > threshold_value.
    If breach_mode == "below", we compare min or value < threshold_value.
    """
    if starttime >= endtime:
        return None, None

    gran_funcs = {
        "hour": squac_client.api_measurement_measurements_list,
        "day": squac_client.api_measurement_day_archives_list,
        "week": squac_client.api_measurement_week_archives_list,
        "month": squac_client.api_measurement_month_archives_list,
    }
    query_func = gran_funcs.get(granularity)
    if not query_func:
        log.error(f"Unknown granularity: {granularity}")
        return None, None

    try:
        log.debug(
            f"QUERY: metric_id={metric_id}, sncl={sncl}, channel={channel_map[sncl]}, "
            f"starttime={starttime}, endtime={endtime}, granularity={granularity}, mode={breach_mode}"
        )
        measurements = query_func(
            metric=[metric_id] if metric_id else [],
            channel=[channel_map[sncl]],
            starttime=starttime,
            endtime=endtime,
        )
    except Exception as e:
        log.error(f"Error querying {granularity} data for SNCL '{sncl}': {e}")
        return None, None

    if not measurements:
        log.debug(f"No data returned for {sncl} in {granularity} {starttime}–{endtime}.")
        return None, None

    # Channel type
    chantype = sncl.split(".")[3][:2]
    threshold_value = threshold_dict.get(chantype)
    if threshold_value is None:
        log.warning(f"No threshold found for channel type '{chantype}'.")
        return None, None

    latest_breach_time = None
    latest_breach_value = None

    # Helper function to get the relevant measurement for "above" or "below"
    def get_relevant_measurement_fields(m):
        """
        Return (val, tstamp) according to breach_mode.
        If breach_mode == "above", use m.max if present, else m.value.
        If breach_mode == "below", use m.min if present, else m.value.
        """
        if breach_mode == "above":
            if hasattr(m, "max"):
                return m.max, m.starttime
            elif hasattr(m, "value"):
                return m.value, m.starttime
            else:
                return None, None
        else:  # "below"
            if hasattr(m, "min"):
                return m.min, m.starttime
            elif hasattr(m, "value"):
                return m.value, m.starttime
            else:
                return None, None

    # Compare function
    def compare(val, threshold):
        if breach_mode == "above":
            return (val is not None) and (val > threshold)
        else:  # "below"
            return (val is not None) and (val < threshold)

    for meas in measurements:
        val, tstamp = get_relevant_measurement_fields(meas)
        if val is None or tstamp is None:
            log.debug(f"Measurement lacks relevant field for mode={breach_mode}: {meas}")
            continue

        if compare(val, threshold_value):
            # Keep the LATEST time
            if latest_breach_time is None or tstamp > latest_breach_time:
                # Ensure we never report a time < T1
                if tstamp < T1:
                    continue
                latest_breach_time = tstamp
                latest_breach_value = val

    return latest_breach_time, latest_breach_value


###############################################################################
# Internal Helper: _get_granularity_bounds
###############################################################################

def _get_granularity_bounds(timestamp, granularity, T1, T2):
    """
    Given a 'timestamp' and a granularity ('hour', 'day', 'week', 'month'),
    return (start, end) that defines that entire block, then clamp to T2.

    Example logic (simplified):
      - hour: e.g. 12:00–12:59
      - day:  e.g. 00:00–23:59:59
      - week: e.g. 7 days after the timestamp
      - month: entire month (1st → last day)

    """
    if granularity == "hour":
        start = timestamp.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=59, seconds=59)

    elif granularity == "day":
        start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=23, minutes=59, seconds=59)

    elif granularity == "week":
        start = timestamp
        end = timestamp + timedelta(days=7, seconds=-1)

    elif granularity == "month":
        month_start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month_start.month % 12) + 1
        year = month_start.year + (month_start.month // 12)
        month_end = month_start.replace(month=next_month, year=year) - timedelta(seconds=1)
        start, end = month_start, month_end

    else:
        # fallback to hourly approach
        start = timestamp.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=59, seconds=59)

    # Clamp to user T2
    if end > T2:
        end = T2
    if start > end:
        start, end = end, end

    return (start, end)

