# importing the required module
import matplotlib.pyplot as plt
import math
import numpy as np
import datetime
import pandas as pd

# import output from sim_data
from sim_data import output

def make_graph(start_time, end_time, y_vals, output_name):
    # x = np.array(pd.date_range(start=start_time,end=end_time))
    x = [n for n in pd.date_range(start=start_time,end=end_time)]
    # length = max(len(y_vals), len(x))
    # plt.xticks([0, 1, 2],['2018','2019','2020'], rotation=20)
    plt.figure(figsize=(10,5))
    plt.xticks(rotation=40)
    # plt.xaxis.set_minor_locator(MultipleLocator(5))
    plt.minorticks_on()
    plt.plot(x, y_vals)
    
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')

    plt.title(output_name)

    plt.savefig('./output/' + output_name + '.png')
    plt.clf()


def main():
    start = datetime.datetime(2006, 1, 1)
    end =  datetime.datetime(2021, 8, 31)

    make_graph(start, end, output.y_vals, "graph")


if __name__ == "__main__":
    main()