# importing the required module
import matplotlib.pyplot as plt
import math
import numpy as np
import datetime
import pandas as pd

# import output from sim_data

def make_graph(start_time, end_time, y_vals, output_name):
    SPY_data = pd.read_csv("./SPY_Prices.csv")
    relevant_SPY_data = SPY_data[(SPY_data["date"] >= str(start_time.date())) & (SPY_data["date"] <= str(end_time.date()))]
    t = [n for n in pd.date_range(start=start_time,end=end_time)]

    fig, ax1 = plt.subplots(figsize=(20, 5))
    plt.minorticks_on()

    color = 'tab:red'
    ax1.set_xlabel('time')
    ax1.set_ylabel('Portfolio Value', color=color)
    ax1.plot(t, y_vals, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('SPY', color=color)  # we already handled the x-label with ax1
    ax2.plot(t, relevant_SPY_data["price"], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    # plt.show()

    plt.title(output_name)
    plt.savefig('./output/' + output_name + '.png')



    # # Set up figure
    # plt.xticks(rotation=40)
    # plt.xlabel('Time')
    # plt.ylabel('Portfolio Value')
    # # Plot portfolio
    # x = [n for n in pd.date_range(start=start_time,end=end_time)]
    # plt.plot(x, y_vals, label="Portfolio")
    # # Plot SPY
    # SPY_data = pd.read_csv("./SPY_Prices.csv")
    # relevant_SPY_data = SPY_data[(SPY_data["date"] >= str(start_time.date())) & (SPY_data["date"] <= str(end_time.date()))]
    # plt.plot(x, relevant_SPY_data["price"], label="SPY")
    
    # plt.legend()
    # plt.savefig('./output/' + output_name + '.png')
    # plt.clf()


def main():
    start = datetime.datetime(2005, 1, 10)
    end =  datetime.datetime(2021, 9, 2)

    make_graph(start, end, output.y_vals, "graph")


if __name__ == "__main__":
    main()