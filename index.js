require("dotenv").config();
const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
const app = express();
const router = require("./router");
const port = process.env.PORT || 5000;
const connection = require("./connection");
const { spawn } = require("child_process");
//크롤링 및 분석 후에 최종 res.send로 프론트에 전달해야 함.
//json parsing하는데에 변수가 많음.

app.use(cors());
// "Origin, X-Requested-With, Content-Type, Accept"
app.all("/*", function (req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "X-Requested-With");
  next();
});
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

connection.getConnection(function (err, connection) {
  if (!err) {
    console.log("getConnected");
  }
  connection.release();
});

app.post("/recommendation", (req, res) => {
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

app.post("/add_diy", (req, res) => {
  let sql = `INSERT INTO diy_reco_history(user_no, w_1st, w_2nd, w_3rd, w1, w2, w3, w4, w5, total_w, Q1, Q2, Q3, Q4, Q5, univ_lat, univ_lon, T_set ) values (${req.body.user_no}, ${req.body.w_1st}, ${req.body.w_2nd}, ${req.body.w_3rd}, ${req.body.w1}, ${req.body.w2}, ${req.body.w3}, ${req.body.w4}, ${req.body.w5}, ${req.body.total_w},'${req.body.Q1}', ${req.body.Q2},'${req.body.Q3}','${req.body.Q4}','${req.body.Q5}',${req.body.univ_lat},${req.body.univ_lon}, '${req.body.T_set};
  ')`;

  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
    console.log(err);
  });
});

app.post("/add_eval", (req, res) => {
  let sql = `INSERT INTO evaluation(evaluation_category_no, univ_name, T_set, rank01_score, rank02_score, rank03_score, rank04_score, rank05_score) values (${req.body.evaluation_category_no}, '${req.body.univ_name}', '${req.body.T_set}', ${req.body.rank01_score}, ${req.body.rank02_score}, ${req.body.rank03_score}, ${req.body.rank04_score}, ${req.body.rank05_score})`;

  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
    console.log(err);
  });
});
app.listen(port, () =>
  console.log(`Example app listening on port 
${port}!`)
);
app.use(router);
