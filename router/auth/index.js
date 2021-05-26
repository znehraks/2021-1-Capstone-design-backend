const express = require("express");
const connection = require("../../connection");
const app = express();
//palettea_user(C R U D) (/api/users)

//회원가입
app.post("/join", (req, res) => {
  let sql = `
    `;
  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
    console.log(err);
  });
});

//로그인
app.get("/login", (req, res) => {
  let sql = `
      `;
  connection.query(sql, (err, rows, fields) => {
    res.send(rows);
    console.log(err);
  });
});

module.exports = app;
