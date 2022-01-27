import "./App.css";
import APICaller from "./APICaller";
import React, { useEffect, useState, useCallback } from "react";
import Button from "react-bootstrap/Button";
import ButtonGroup from "react-bootstrap/ButtonGroup";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import InputGroup from "react-bootstrap/InputGroup";
import FormControl from "react-bootstrap/FormControl";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";

import { ImStatsDots } from "react-icons/im";


import MyLineChart from "./Components/MyLineChart";

function App() {
  let [dataState, updateData] = useState([]);
  let [chartSizeState, updateChartSize] = useState([600, 300]);

  let [paramsState, updateParams] = useState({
    "start":"2005-01-10",
    "end":"2021-01-10",
    "name":"Strategy Name",
    "hedge":0.03,
    "rebalancing_period":365,
    "expiry":120,
    "target_delta":-0.01,
    "hedge_fragmentation":24,
    "rollover":15,
    "trade_frequency":15

  });

  const [confirmParams, setConfirmParams] = useState(false);
  const [paramsError, setParamsError] = useState(false);
  const [paramsErrorContent, setParamsErrorContent] = useState([]);

  const [loadingState, setLoadingState] = useState(false);

  const [overviewState, setOverviewState] = useState(false);
  const [strategyState, setStrategyState] = useState({});
  const [statsState, setStatsState] = useState({});

  async function callAPI(params) {
    let data = await APICaller.runSimulation(params);
    // console.log(data["stats"])
    updateData(data["datapoints"]);
    setStatsState(data["stats"]);
    setStrategyState(paramsState);
    setConfirmParams(false);
    setLoadingState(false);
  }

  function updateForm(e, data) {
    let id = e.target.id;
    let temp = paramsState;
    temp[id] = e.target.value;

    if (e.target.value.length < 1) {
      delete temp[id];
    }

    updateParams(temp);
  }

  function validateParams() {
    /*
"start" not in params or "end" not in params or "name" not in params or "hedge" not in params or "rebalancing period" not in params \
            or "target delta" not in params or "expiry" not in params or "rollover" not in params \
            or "hedge fragmentation" not in params:
    */
    let errors = [];
    let foundError = false;
    if (paramsState["start"] == undefined) {
      errors.push("start is undefined");
      foundError = true;
    }
    if (
      paramsState["start"] > "2021-01-10" ||
      paramsState["start"] < "2005-01-10" ||
      paramsState["end"] > "2021-01-10" ||
      paramsState["end"] < "2005-01-10"
    ) {
      errors.push("Start and end must be between 2005-01-10 and 2021-01-10 ");
      foundError = true;
    }
    if (paramsState["end"] == undefined) {
      errors.push("end is undefined");
      foundError = true;
    }
    if (paramsState["name"] == undefined) {
      errors.push("name is undefined");
      foundError = true;
    }
    if (paramsState["hedge"] == undefined) {
      errors.push("hedge is undefined");
      foundError = true;
    }
    if (
      parseFloat(paramsState["hedge"]) < 0 ||
      parseFloat(paramsState["hedge"]) > 1
    ) {
      errors.push("Hedge must be between 0 and 1 (ex. 0.02 or 0.5)");
      foundError = true;
    }
    if (paramsState["rebalancing_period"] == undefined) {
      errors.push("rebalancing is undefined");
      foundError = true;
    }
    if (paramsState["target_delta"] == undefined) {
      errors.push("delta is undefined");
      foundError = true;
    }
    if (
      parseFloat(paramsState["target_delta"]) > 0 ||
      parseFloat(paramsState["targer_delta"]) < -1
    ) {
      errors.push("delta must be between -1 and 0 (ex. -0.01 or -0.5)");
      foundError = true;
    }
    if (paramsState["expiry"] == undefined) {
      errors.push("expiry is undefined");
      foundError = true;
    }
    if (paramsState["rollover"] == undefined) {
      errors.push("rollover is undefined");
      foundError = true;
    }
    if (paramsState["hedge_fragmentation"] == undefined) {
      errors.push("fragmentation is undefined");
      foundError = true;
    }
    if (paramsState["trade_frequency"] == undefined) {
      errors.push("Trade Frequency is undefined");
      foundError = true;
    }

    if (foundError) {
      setParamsError(true);
      setParamsErrorContent(errors);
    } else {
      // console.log("VALID!!");
      setConfirmParams(true);
    }
  }

  async function runBacktest() {
    setLoadingState(true);
    callAPI(paramsState);
    // console.log(data)
    // updateData(data);
  }

  return (
    <div className="App">
      <Button variant="primary" onClick={() => setOverviewState(true)} style={{"position":"absolute", "top":"50px", "left":"50px"}}>
        <ImStatsDots /> Overview
      </Button>
      <div className="Chart">
        <MyLineChart
          data={dataState}
          size={[chartSizeState[0], chartSizeState[1]]}
        ></MyLineChart>
      </div>

      <div className="Size-Selector">
        <h2>Chart Size:</h2>
        <ButtonGroup aria-label="Basic example">
          <Button
            onClick={() => updateChartSize([600, 300])}
            variant="secondary"
          >
            Small
          </Button>
          <Button
            onClick={() => updateChartSize([800, 500])}
            variant="secondary"
          >
            Medium
          </Button>
          <Button
            onClick={() => updateChartSize([1200, 600])}
            variant="secondary"
          >
            Large
          </Button>
        </ButtonGroup>
      </div>
      <Container>
        <h1>Strategy Parameters:</h1>
        <Row>
          <Col>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">Start Date</InputGroup.Text>
              <FormControl type="date" id="start" onChange={updateForm} defaultValue={paramsState["start"]} />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">End Date</InputGroup.Text>
              <FormControl type="date" id="end" onChange={updateForm} defaultValue={paramsState["end"]} />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">Strategy Name</InputGroup.Text>
              <FormControl
                type="text"
                id="name"
                onChange={updateForm}
                defaultValue={paramsState["name"]}
              />
            </InputGroup>
          </Col>
          <Col>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Hedge Percentage (between 0-1)
              </InputGroup.Text>
              <FormControl
                type="number"
                onChange={updateForm}
                id="hedge"
                defaultValue={paramsState["hedge"]}
              />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Rebalancing Period (in days)
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["rebalancing_period"]}
                type="number"
                onChange={updateForm}
                id="rebalancing_period"
              />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Target Delta (between -1-0)
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["target_delta"]}
                type="number"
                onChange={updateForm}
                id="target_delta"
              />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Trade Frequency
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["trade_frequency"]}
                type="number"
                onChange={updateForm}
                id="trade_frequency"
              />
            </InputGroup>
          </Col>
          <Col>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Expiry (in days)
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["expiry"]}
                type="number"
                onChange={updateForm}
                id="expiry"
              />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Rollover (in days)
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["rollover"]}
                type="number"
                onChange={updateForm}
                id="rollover"
              />
            </InputGroup>
            <InputGroup className="mb-3">
              <InputGroup.Text id="basic-addon3">
                Hedge Fragmentation
              </InputGroup.Text>
              <FormControl
                defaultValue={paramsState["hedge_fragmentation"]}
                type="number"
                onChange={updateForm}
                id="hedge_fragmentation"
              />
            </InputGroup>
          </Col>
        </Row>
        <Button variant="primary" onClick={validateParams}>
          Backtest
        </Button>
      </Container>
      <Modal show={confirmParams} onHide={() => setConfirmParams(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Parameters</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ul>
            <li>Name: {paramsState.name}</li>
            <li>Start: {paramsState.start}</li>
            <li>End: {paramsState.end}</li>
            <li>Hedge Percentage: {paramsState["hedge_percentage"]}</li>
            <li>Rebalancing Period: {paramsState["rebalancing_period"]}</li>
            <li>Target Delta: {paramsState["target_delta"]}</li>
            <li>Expiry: {paramsState["expiry"]}</li>
            <li>Rollover: {paramsState["rollover"]}</li>
            <li>Hedge Fragmentation: {paramsState["hedge_fragmentation"]}</li>
          </ul>
        </Modal.Body>
        <Modal.Footer>
          {loadingState ? (
            <Button variant="primary">
              <Spinner
                as="span"
                animation="grow"
                size="sm"
                role="status"
                aria-hidden="true"
              />
              Loading...
            </Button>
          ) : (
            <Button variant="primary" onClick={runBacktest}>
              Confirm and Backtest
            </Button>
          )}
        </Modal.Footer>
      </Modal>
      <Modal show={paramsError} onHide={() => setParamsError(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Parameters Error</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Please fix the following errors:
          <ul>
            {paramsErrorContent.map((err) => {
              return <li key={err}>{err}</li>;
            })}
          </ul>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={() => setParamsError(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={overviewState} onHide={() => setOverviewState(false)} size="lg"
        aria-labelledby="contained-modal-title-vcenter">
        <Modal.Header closeButton>
          <Modal.Title>Overview</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row>
            <Col>
            <h3>Strategy Parameters</h3>
              <ul>
                <li>SPY %: {1 - strategyState["hedge"]},</li>
                <li>Hedge %: {strategyState["hedge"]},</li>
                <li>Rebalancing Period: {strategyState["rebalancing_period"]},</li>
                <li>Days to Expiry: {strategyState["expiry"]},</li>
                <li>Rollover: {strategyState["rollover"]},</li>
                <li>Target Delta: {strategyState["target_delta"]},</li>
                <li>Trade Frequency: {strategyState["trade_frequency"]},</li>
              </ul>
            </Col>
            <Col>
            <h3>Statistics</h3>
              <ul>
                <li>Number of days: {statsState["# of days"]},</li>
                <li>Number of SPY trades: {statsState["# of SPY trades"]},</li>
                <li>
                  Number of SPY shares bought:
                  {statsState["# of SPY shares bought"]},
                </li>
                <li>Number of put trades: {statsState["# of put trades"]},</li>
                <li>
                  Number of put contracts bought:
                  {statsState["# of put contracts bought"]},
                </li>
                <li>Largest % drawdown: {statsState["largest % drawdown"]}</li>
                <li>Largest % drawup: {statsState["largest % drawup"]}</li>
                <li>
                  Avg. profit per day: {statsState["avg. profit per day"]}
                </li>
                <li>Total profit: {statsState["total profit"]}</li>
              </ul>
            </Col>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={() => setOverviewState(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default App;
