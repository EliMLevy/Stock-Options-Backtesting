# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from backtester import (backtest, load_data)
from noHedge import backtestNoHedge
from datetime import datetime
import pandas as pd
import json


hostName = "localhost"
serverPort = 8090
data = {}

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = self.path.split("?")
        if len(parsed_path) > 1:
            params = self.parse_path_toDict(self.path)
        else:
            params = {}
        """
        {
            "start":
            "end":
            "name": "No_Hedge",
            "hedge": 0,   
            "rebalancing period": 365,   
            "target delta": [-0.03, -0.01]
            "expiry": 120,   
            "rollover": 60,   
            "hedge fragmentation": 1,
            "trade frequency": 15
        }

        """
        if "start" not in params or "end" not in params or "name" not in params or "hedge" not in params or "rebalancing period" not in params \
            or "target delta" not in params or "expiry" not in params or "rollover" not in params \
            or "hedge fragmentation" not in params or "trade frequency" not in params:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Incomplete parameters</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>Params incomplete</p>", "utf-8"))
            self.wfile.write(bytes("<p>You sent "+ str(params) + " </p>", "utf-8"))
            self.wfile.write(bytes("<p>Required: start, end, name, hedge, rebalancing period, target delta, expiry, rollover, hedge fragmentation, trade frequency</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        else:
            strategy = self.fix_params(params)
            params = {
                "start": strategy["start"],
                "end": strategy["end"],
                "starting balance": 100000, 
                "strategy": strategy,
                "verbose": False
            }
            # print(params)
            noHedge = backtestNoHedge(params, data)
            output = backtest(params, data)
            # print(output["y axis"])
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "stats": output["stats"],
                "no hedge": noHedge["y axis"],
                "y vals": output["y axis"],
                "x vals": [str(n.date()) for n in pd.date_range(start=params["start"],end=params["end"])],
                "hedge pl": output["hedge pl"]
            }
            self.wfile.write(bytes(json.dumps(response), "utf-8"))


    def parse_path_toDict(self, path):
        parsed_path = self.path.split("?")
        query_string = parsed_path[1]
        # print(query_string)
        query_string = query_string.replace("_", " ")
        parsed_queries = query_string.split("&")
        params = {}
        if len(parsed_queries) > 1:
            for query in parsed_queries:
                [key, value] = query.split("=")
                params[key] = value
        return params
    
    def fix_params(self, params):
        result = {
            "start": datetime.strptime(params["start"], "%Y-%m-%d"),
            "end": datetime.strptime(params["end"], "%Y-%m-%d"),
            "name": str(params["name"]),
            "SPY": 1 - float(params["hedge"]),
            "hedge": float(params["hedge"]),   
            "rebalancing period": int(365),   
            "target delta": [float(params["target delta"]) - 0.02, float(params["target delta"]) ],
            "expiry": int(params["expiry"]),   
            "rollover": int(params["rollover"]),   
            "hedge fragmentation": int(params["hedge fragmentation"]),
            "trade frequency": int(params["trade frequency"])
        }

        return result


if __name__ == "__main__":  
    print("loading data...")
    data = load_data(datetime(2005, 1, 10), datetime(2021, 1, 10))
    print("data loaded.")
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
