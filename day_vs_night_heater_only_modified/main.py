import secrets
import logging
import math
import os
import tables

from influxdb import DataFrameClient
import numpy as np
import matplotlib.mlab as mlab
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from tqdm import tqdm
import matplotlib.mlab as mlab

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Need to ssh tunnel for this to work
# ssh -L 8086:localhost:8086 aq.byu.edu -N
influx = DataFrameClient(
    host=secrets.HOST,
    port=secrets.PORT,
    username=secrets.USERNAME,
    password=secrets.PASSWORD,
    database=secrets.DATABASE,
)


def large_query(influx, measurement, query, total=None, limit=100_000):
    if total is not None:
        total = math.ceil(total / limit)

    with tqdm(total=total) as pbar:
        offset = 0
        while True:
            new_query = query + " LIMIT {} OFFSET {}".format(limit, offset)
            data = influx.query(new_query)
            data = data[measurement]

            received = len(data)
            pbar.update(1)

            yield data

            offset += limit
            if received != limit:
                break


def load_data(filename):
    if os.path.exists(filename):
        LOGGER.info("Loading cached data...")
        return pd.read_hdf(filename)

    LOGGER.info("Downloading data...")
    result = influx.query(
        "SELECT COUNT(sequence) FROM air_quality_sensor WHERE time > '2019-10-01' AND time <= now()"
    )
    count = result["air_quality_sensor"].values[0][0]

    queries = large_query(
        influx,
        "air_quality_sensor",
        "SELECT * FROM air_quality_sensor WHERE time > '2019-10-01' AND time <= now()",
        count,
    )

    all_data = pd.concat(list(queries), sort=False)
    all_data.to_hdf(filename, "data")
    return all_data


data = load_data("aq_data.h5")
LOGGER.info("Done loading data...")

'''
# https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
# https://stackoverflow.com/questions/18172851/deleting-dataframe-row-in-pandas-based-on-column-value
data = data[data.voltage > 0]
data = data[data.location_name == 'Mongolia']

days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# for testing ...
for day in days_of_week:
    plt.xlabel('Sensors for {0}'.format(day))
    plt.ylabel('PM 2.5 Value')
    plt.title('Week PM 2.5 for sensors for {0}'.format(day))
    plt.grid(True)
    sensors_data = list()
    sensors_name = list()
    temp = data[data.index.day_name() == day]
    # temp = temp.groupby("name")
    for name, sensor_data in temp.groupby("name"):
        sensors_name.append(name)
        sensors_data.append(temp.groupby("name").get_group(name)["pm2_5"].between_time('01:01', '07:59').to_numpy().tolist())

    results = plt.boxplot(sensors_data, showfliers=False, labels=sensors_name, showmeans=True, meanline=True)
    print('whiskers: ', [item.get_ydata()[1] for item in results['whiskers']])
    print('caps: ', [item.get_ydata()[1] for item in results['caps']])
    print('boxes: ', [item.get_ydata()[1] for item in results['boxes']])
    print('medians: ', [item.get_ydata()[1] for item in results['medians']])
    print('means: ', [item.get_ydata()[1] for item in results['means']])
    print('fliers: ', [item.get_ydata()[1] for item in results['fliers']])
    plt.show()

monday = data[data.index.day_name() == 'Monday']['pm2_5']
tuesday = data[data.index.day_name() == 'Tuesday']['pm2_5']
wednesday = data[data.index.day_name() == 'Wednesday']['pm2_5']
thursday = data[data.index.day_name() == 'Thursday']['pm2_5']
friday = data[data.index.day_name() == 'Friday']['pm2_5']
saturday = data[data.index.day_name() == 'Saturday']['pm2_5']
sunday = data[data.index.day_name() == 'Sunday']['pm2_5']
all_days = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]

print(data)

# https://pythonspot.com/matplotlib-histogram/

num_bins = 5
n, bins, patches = plt.hist(data.voltage.values, num_bins, facecolor='blue', alpha=0.5)
plt.show()

# n, bins, patches = plt.hist(x, num_bins, density=1, facecolor='blue', alpha=0.5)
# plt.show()

# example data
# mu = 100 # mean of distribution
# sigma = 15 # standard deviation of distribution
# # x = mu + sigma * np.random.randn(10000)
#
# num_bins = 20
# # the histogram of the data
# n, bins, patches = plt.hist(data.voltage.values, num_bins, normed=1, facecolor='blue', alpha=0.5)
#
# # add a 'best fit' line
# y = mlab.normpdf(bins, mu, sigma)
# plt.plot(bins, y, 'r--')
# plt.xlabel('Smarts')
# plt.ylabel('Probability')
# plt.title(r'Histogram of IQ: $\mu=100$, $\sigma=15$')
#
# # Tweak spacing to prevent clipping of ylabel
# plt.subplots_adjust(left=0.15)
# plt.show()
'''