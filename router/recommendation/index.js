const express = require("express");
const { spawn } = require("child_process");
const app = express();
app.post("/", (req, res) => {
  try {
    var data;
    //   var largeDataset = [];
    // spawn new child process to call the python script
    const python = spawn("python", [
      "cal_weight.py",
      req.body.univ_name, //1
      req.body.univ_lon, //2
      req.body.univ_lat, //3
      req.body.Q2Answer, //4
      req.body.Q3Answer, //5
      req.body.Q4Answer, //6
      req.body.Q5Answer, //7
      req.body.w1, //8
      req.body.w2, //9
      req.body.w3, //10
      req.body.w4, //11
      req.body.w5, //12
    ]);
    // collect data from script
    python.stdout.on("data", function (chunk) {
      // console.log("Pipe data from python script ...");
      // largeDataset.push(data);

      data = chunk.toString("utf-8");
      res.json(data);
    });

    // in close event we are sure that stream from child process is closed
    python.on("close", (code) => {
      console.log(`child process close all stdio with code ${code}`);
      // send data to browser
      // const obj = JSON.parse(data);
    });
  } catch (e) {}
});

module.exports = app;
