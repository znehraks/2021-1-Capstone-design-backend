const express = require("express");
const connection = require("../../connection");
const app = express();
//palettea_user(C R U D) (/api/users)

app.get("/get_diy", (req, res) => {
  let sql = "SELECT * FROM diy_reco_history where is_deleted = 0";
  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
  });
});

app.post("/add_diy", (req, res) => {
  let sql = `INSERT INTO diy_reco_history(user_no, w_1st, w_2nd, w_3rd, w1, w2, w3, w4, w5, total_w, Q1, Q2, Q3, Q4, Q5, univ_lat, univ_lon, T_set ) values (${req.body.user_no}, ${req.body.w_1st}, ${req.body.w_2nd}, ${req.body.w_3rd}, ${req.body.w1}, ${req.body.w2}, ${req.body.w3}, ${req.body.w4}, ${req.body.w5}, ${req.body.total_w},'${req.body.Q1}', ${req.body.Q2},'${req.body.Q3}','${req.body.Q4}','${req.body.Q5}',${req.body.univ_lat},${req.body.univ_lon}, '${req.body.T_set};
  
  ')`;

  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
    console.log(err);
  });
});

module.exports = app;
