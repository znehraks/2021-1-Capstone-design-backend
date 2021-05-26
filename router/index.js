const express = require("express");
const router = express.Router();
const auth = require("./auth");
const recommendation = require("./recommendation");
const history = require("./history");
const app = express();

//url Routing
router.use("/api/auth", auth);
router.use("/api/recommendation", recommendation);
router.use("/api/history", history);

module.exports = router;
