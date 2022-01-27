# importing the required module
import matplotlib.pyplot as plt
import math
import numpy as np
import datetime
import pandas as pd
import json


# import output from sim_data

def make_graph(start_time, end_time, y_vals, output_name, no_hedge_y_vals):
    # Set up figure
    plt.title(output_name)
    plt.figure(figsize=(20,10))
    plt.xticks(rotation=40)
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    plt.minorticks_on()
    x = [n for n in pd.date_range(start=start_time,end=end_time)]
    # Plot portfolio
    plt.plot(x, y_vals, label="With Hedge")
    if no_hedge_y_vals is not None:
        plt.plot(x, no_hedge_y_vals, label="No Hedge")
    
    plt.legend()
    plt.savefig('./output/' + output_name + '.png')
    plt.clf()


def main():
    start_time =  datetime.datetime(2005, 1, 10)
    end_time = datetime.datetime(2021, 1, 10)
    y_val = json.load(open("./output/Investigation_hedgePL.json"))
    make_graph(start_time, end_time, y_val, "HedgePL", None)


if __name__ == "__main__":
    main()