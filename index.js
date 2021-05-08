const express = require("express");
const bodyParser = require("body-parser");
const { spawn } = require("child_process");
const app = express();
const port = 5000;
//크롤링 및 분석 후에 최종 res.send로 프론트에 전달해야 함.
//json parsing하는데에 변수가 많음.

// "Origin, X-Requested-With, Content-Type, Accept"

app.use(function (req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header(
    "Access-Control-Allow-Headers",
    "Origin, X-Requested-With, Content-Type, Accept"
  );
  next();
});

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

String.prototype.replaceAll = function (org, dest) {
  return this.split(org).join(dest);
};
app.post("/recommendation", (req, res) => {
  try {
    var data;
    //   var largeDataset = [];
    // spawn new child process to call the python script
    const python = spawn("python", [
      "cal_weight.py",
      req.body.univ_name,
      req.body.univ_lat,
      req.body.univ_lon,
      req.body.Q2Answer,
      req.body.w1,
      req.body.w2,
      req.body.w3,
      req.body.w4,
      req.body.w5,
    ]);
    // collect data from script
    python.stdout.on("data", function (chunk) {
      // console.log("Pipe data from python script ...");
      // largeDataset.push(data);

      data = chunk.toString("utf-8");
      data = data.replaceAll("'", '"');
      data = data.replaceAll("None", '"None"');
    });

    // in close event we are sure that stream from child process is closed
    python.on("close", (code) => {
      console.log(`child process close all stdio with code ${code}`);
      // send data to browser
      const obj = JSON.parse(data);
      res.json(obj);
    });
  } catch (e) {}
});
app.listen(port, () =>
  console.log(`Example app listening on port 
${port}!`)
);
