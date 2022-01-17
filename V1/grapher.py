# importing the required module
import matplotlib.pyplot as plt
import math
import numpy as np
import datetime
import pandas as pd

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
    # Plot SPY
    # SPY_data = pd.read_csv("./SPY_Prices.csv")
    # relevant_SPY_data = SPY_data[(SPY_data["date"] >= str(start_time.date())) & (SPY_data["date"] <= str(end_time.date()))]
    # translated_SPY_values = relevant_SPY_data["value"] - (relevant_SPY_data["value"].iloc[0] - y_vals[0])
    plt.plot(x, no_hedge_y_vals, label="No Hedge")
    
    plt.legend()
    plt.savefig('./output/' + output_name + '.png')
    plt.clf()


def main():
    start_time =  datetime.datetime(2007, 1, 10)
    end_time = datetime.datetime(2011, 1, 10)

    # Set up figure
    plt.figure(figsize=(10,5))
    plt.xticks(rotation=40)
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    # Plot portfolio
    x = [n for n in pd.date_range(start=start_time,end=end_time)]
    # Plot SPY
    SPY_data = pd.read_csv("./SPY_Prices.csv")
    relevant_SPY_data = SPY_data[(SPY_data["date"] >= str(start_time.date())) & (SPY_data["date"] <= str(end_time.date()))]
    translated_SPY_values = relevant_SPY_data["value"] - (relevant_SPY_data["value"].iloc[0] - 100000)
    plt.plot(x, translated_SPY_values, label="SPY")
    
    plt.legend()
    plt.savefig('./output/' + "TESTING" + '.png')
    plt.clf()


if __name__ == "__main__":
    main()