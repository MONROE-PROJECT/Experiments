/*
 * This script imports log data from dashc, calculates a number of quality
 * criteria, and exports results to disk. Some criteria are defined as
 * distributions, others as averages or relative percentages.
 */

DROP TABLE IF EXISTS raw_data CASCADE;

-- Base directories

\set import_dir .
\set export_dir .

-- Import file(s)

\set raw_data :import_dir/dashc.csv

-- Export file(s)

\set stations           :export_dir/stations.csv
\set del_rate           :export_dir/del_rate.csv
\set act_rate           :export_dir/act_rate.csv
\set buff_level         :export_dir/buff_level.csv
\set states             :export_dir/states.csv
\set bitrates           :export_dir/bitrates.csv
\set startups           :export_dir/startups.csv
\set startups_quartiles :export_dir/startups_quartiles.csv
\set startups_outliers  :export_dir/startups_outliers.csv
\set startups_limits    :export_dir/startups_limits.csv
\set switches           :export_dir/switches.csv
\set switches_quartiles :export_dir/switches_quartiles.csv
\set switches_outliers  :export_dir/switches_outliers.csv
\set switches_limits    :export_dir/switches_limits.csv
\set stalls             :export_dir/stalls.csv
\set stalls_quartiles   :export_dir/stalls_quartiles.csv
\set stalls_outliers    :export_dir/stalls_outliers.csv
\set stalls_limits      :export_dir/stalls_limits.csv

-- Settings

\set period_duration  '300'
\set period_count     '20'
\set batch_size       '10'
\set segment_duration '2'

-- Import data

CREATE TABLE raw_data (
    period     integer, -- Custom
    id         integer, -- Custom
    seg        integer,
    arr_time   integer,
    del_time   integer,
    act_time   integer, -- Custom
    stall_dur  integer,
    rep_level  integer,
    del_rate   integer,
    act_rate   integer,
    byte_size  integer,
    buff_level numeric
);

COPY raw_data (
    id,
    seg,
    arr_time,
    del_time,
    stall_dur,
    rep_level,
    del_rate,
    act_rate,
    byte_size,
    buff_level
)
FROM :'raw_data' CSV HEADER;

-- Preprocess data

UPDATE raw_data
SET period   = ((id - 1) / :batch_size)
               + (arr_time / (1000 * :period_duration))
               + 1,
    act_time = 1000 * :period_duration * ((id - 1) / :batch_size)
               + arr_time;

DELETE FROM raw_data
WHERE period > :period_count;

-- Number of stations (n)

CREATE VIEW stations AS
    WITH intervals AS (
        SELECT generate_series(0, 6000 - 60, 60) AS time
    )
    SELECT time, (time / :period_duration + 1) * :batch_size AS stations
    FROM intervals
    ORDER BY time;

-- Average delivery rate (kbps)

CREATE VIEW del_rate AS
    SELECT 60 * (act_time / 60000) AS time,
           round(AVG(del_rate) :: numeric, 3) AS del_rate
    FROM raw_data
    GROUP BY time
    ORDER BY time;

-- Average actual rate (kbps)

CREATE VIEW act_rate AS
    SELECT 60 * (act_time / 60000) AS time,
           round(AVG(act_rate) :: numeric, 3) AS act_rate
    FROM raw_data
    GROUP BY time
    ORDER BY time;

-- Average buffer level (seconds)

CREATE VIEW buff_level AS
    SELECT 60 * (act_time / 60000) AS time,
           round(AVG(buff_level) :: numeric, 3) AS buff_level
    FROM raw_data
    GROUP BY time
    ORDER BY time;

-- Relative duration of player states (percent)

CREATE VIEW states AS
    WITH states AS (
        SELECT period,
               1000 * :segment_duration * COUNT(*) AS playing,
               SUM(stall_dur) AS stalling,
               1000 * :segment_duration * COUNT(*) + SUM(stall_dur) AS sum_
        FROM raw_data
        GROUP BY period
    )
    SELECT period,
           round(100 * playing / sum_ :: numeric, 3) AS playing,
           round(100 * stalling / sum_ :: numeric, 3) AS stalling
    FROM states
    ORDER BY period;

-- Relative duration of bit rate levels (percent)

CREATE VIEW bitrates AS
    WITH totals AS (
        SELECT period,
               1000 * :segment_duration * COUNT(*) AS duration
        FROM raw_data
        GROUP BY period
    ), bitrates AS (
        SELECT period,
               rep_level,
               1000 * :segment_duration * COUNT(*) AS duration
        FROM raw_data
        GROUP BY period, rep_level
    ), all_levels AS (
        SELECT bitrates.period,
               rep_level,
               round(100 * bitrates.duration / totals.duration :: numeric, 3)
                   AS percent
        FROM totals, bitrates
        WHERE totals.period = bitrates.period
    ), low AS (
        SELECT period, percent
        FROM all_levels
        WHERE rep_level = '1002'
    ), medium AS (
        SELECT period, percent
        FROM all_levels
        WHERE rep_level = '4002'
    ), high AS (
        SELECT period, percent
        FROM all_levels
        WHERE rep_level = '6002'
    )
    SELECT low.period,
           low.percent AS low,
           medium.percent AS medium,
           high.percent AS high
    FROM low, medium, high
    WHERE low.period = medium.period
      AND medium.period = high.period
    ORDER BY period;

-- Start-up time (seconds)

CREATE VIEW startups AS
    SELECT period, id, round(del_time / 1000 :: numeric, 3) AS del_time
    FROM raw_data
    WHERE seg = 1
    ORDER BY period;

CREATE VIEW startups_quartiles AS
    SELECT period,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY del_time) AS q1,
           percentile_cont(0.5)  WITHIN GROUP (ORDER BY del_time) AS median_,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY del_time) AS q3
    FROM startups
    GROUP BY period
    ORDER BY period;

CREATE VIEW startups_inliers AS
    SELECT startups.period, id, del_time
    FROM startups, startups_quartiles
    WHERE startups.period = startups_quartiles.period
      AND del_time BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW startups_outliers AS
    SELECT startups.period, id, del_time
    FROM startups, startups_quartiles
    WHERE startups.period = startups_quartiles.period
      AND del_time NOT BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW startups_limits AS
    SELECT startups.period,
           MIN(startups.del_time) AS min_,
           MIN(startups_inliers.del_time) AS low,
           MAX(startups_inliers.del_time) AS high,
           MAX(startups.del_time) AS max_
     FROM startups, startups_inliers
     WHERE startups.period = startups_inliers.period
     GROUP BY startups.period
     ORDER BY period;

-- Frequency of quality switches (n per minute)

CREATE VIEW switches AS
    WITH odd AS (
        SELECT period, id, seg, rep_level
        FROM raw_data
        WHERE seg % 2 = 1
    ), even AS (
        SELECT period, id, seg, rep_level
        FROM raw_data
        WHERE seg % 2 = 0
    ), stations AS (
        SELECT period, id
        FROM raw_data
        GROUP BY period, id
    ), levels AS (
        SELECT odd.period,
               odd.id,
               odd.seg,
               odd.rep_level AS current_rep_level,
               even.rep_level AS next_rep_level
        FROM odd, even
        WHERE odd.id = even.id AND odd.seg = even.seg - 1
    ), freqs AS (
        SELECT period,
               id,
               round(60 * COUNT(*) / :period_duration :: numeric, 3) AS freq
        FROM levels
        WHERE current_rep_level <> next_rep_level
        GROUP BY period, id
    )
    SELECT stations.period,
           stations.id,
           COALESCE(freq, 0.000) AS freq
    FROM stations LEFT JOIN freqs
    ON stations.period = freqs.period AND stations.id = freqs.id
    ORDER BY period;

CREATE VIEW switches_quartiles AS
    SELECT period,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY freq) AS q1,
           percentile_cont(0.5)  WITHIN GROUP (ORDER BY freq) AS median_,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY freq) AS q3
    FROM switches
    GROUP BY period
    ORDER BY period;

CREATE VIEW switches_inliers AS
    SELECT switches.period, id, freq
    FROM switches, switches_quartiles
    WHERE switches.period = switches_quartiles.period
      AND freq BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW switches_outliers AS
    SELECT switches.period, id, freq
    FROM switches, switches_quartiles
    WHERE switches.period = switches_quartiles.period
      AND freq NOT BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW switches_limits AS
    SELECT switches.period,
           MIN(switches.freq) AS min_,
           MIN(switches_inliers.freq) AS low,
           MAX(switches_inliers.freq) AS high,
           MAX(switches.freq) AS max_
    FROM switches, switches_inliers
    WHERE switches.period = switches_inliers.period
    GROUP BY switches.period
    ORDER BY period;

-- Frequency of stalls (n per minute)

CREATE VIEW stalls AS
    WITH odd AS (
        SELECT period, id, seg, stall_dur
        FROM raw_data
        WHERE seg % 2 = 1
    ), even AS (
        SELECT period, id, seg, stall_dur
        FROM raw_data
        WHERE seg % 2 = 0
    ), stations AS (
        SELECT period, id
        FROM raw_data
        GROUP BY period, id
    ), durations AS (
        SELECT odd.period,
               odd.id,
               odd.seg,
               odd.stall_dur AS current_stall_dur,
               even.stall_dur AS next_stall_dur
        FROM odd, even
        WHERE odd.id = even.id AND odd.seg = even.seg - 1
    ), freqs AS (
        SELECT period,
               id,
               round(60 * COUNT(*) / :period_duration :: numeric, 3) AS freq
        FROM durations
        WHERE current_stall_dur = 0 AND next_stall_dur <> 0
        GROUP BY period, id
    )
    SELECT stations.period AS period,
           stations.id,
           COALESCE(freq, 0.000) AS freq
    FROM stations LEFT JOIN freqs
    ON stations.period = freqs.period AND stations.id = freqs.id
    ORDER BY period;

CREATE VIEW stalls_quartiles AS
    SELECT period,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY freq) AS q1,
           percentile_cont(0.5)  WITHIN GROUP (ORDER BY freq) AS median_,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY freq) AS q3
    FROM stalls
    GROUP BY period
    ORDER BY period;

CREATE VIEW stalls_inliers AS
    SELECT stalls.period, id, freq
    FROM stalls, stalls_quartiles
    WHERE stalls.period = stalls_quartiles.period
      AND freq BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW stalls_outliers AS
    SELECT stalls.period, id, freq
    FROM stalls, stalls_quartiles
    WHERE stalls.period = stalls_quartiles.period
      AND freq NOT BETWEEN q1 - 1.5 * (q3 - q1) AND q3 + 1.5 * (q3 - q1)
    ORDER BY period;

CREATE VIEW stalls_limits AS
    SELECT stalls.period,
           MIN(stalls.freq) AS min_,
           MIN(stalls_inliers.freq) AS low,
           MAX(stalls_inliers.freq) AS high,
           MAX(stalls.freq) AS max_
    FROM stalls, stalls_inliers
    WHERE stalls.period = stalls_inliers.period
    GROUP BY stalls.period
    ORDER BY period;

-- Export data

COPY (SELECT * FROM stations)           TO :'stations'           CSV HEADER;
COPY (SELECT * FROM del_rate)           TO :'del_rate'           CSV HEADER;
COPY (SELECT * FROM act_rate)           TO :'act_rate'           CSV HEADER;
COPY (SELECT * FROM buff_level)         TO :'buff_level'         CSV HEADER;
COPY (SELECT * FROM states)             TO :'states'             CSV HEADER;
COPY (SELECT * FROM bitrates)           TO :'bitrates'           CSV HEADER;
COPY (SELECT * FROM startups)           TO :'startups'           CSV HEADER;
COPY (SELECT * FROM startups_quartiles) TO :'startups_quartiles' CSV HEADER;
COPY (SELECT * FROM startups_outliers)  TO :'startups_outliers'  CSV HEADER;
COPY (SELECT * FROM startups_limits)    TO :'startups_limits'    CSV HEADER;
COPY (SELECT * FROM switches)           TO :'switches'           CSV HEADER;
COPY (SELECT * FROM switches_quartiles) TO :'switches_quartiles' CSV HEADER;
COPY (SELECT * FROM switches_outliers)  TO :'switches_outliers'  CSV HEADER;
COPY (SELECT * FROM switches_limits)    TO :'switches_limits'    CSV HEADER;
COPY (SELECT * FROM stalls)             TO :'stalls'             CSV HEADER;
COPY (SELECT * FROM stalls_quartiles)   TO :'stalls_quartiles'   CSV HEADER;
COPY (SELECT * FROM stalls_outliers)    TO :'stalls_outliers'    CSV HEADER;
COPY (SELECT * FROM stalls_limits)      TO :'stalls_limits'      CSV HEADER;
