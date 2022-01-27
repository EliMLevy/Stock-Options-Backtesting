// import { LineChart, Line } from 'recharts';
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

import React, { useEffect } from "react";

function MyLineChart(props) {
  const data = props.data;

  return (
    <div>
      <LineChart
        width={props.size[0]}
        height={props.size[1]}
        data={data}
        margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
      >
        <Line
          type="linear"
          dot={false}
          dataKey="Portfolio Value"
          stroke="#8884d8"
        />
        <Line type="linear" dot={false} dataKey="No Hedge" stroke="#00fff7" />
        <CartesianGrid stroke="#ccc" strokeDasharray="5 5" />
        <XAxis dataKey="Date" />
        <YAxis />
        <Tooltip />
      </LineChart>

      {/* <LineChart width={400} height={400} data={data}>
            <Line type="monotone" dataKey="uv" stroke="#8884d8" />
          </LineChart> */}
    </div>
  );
}

export default MyLineChart;
