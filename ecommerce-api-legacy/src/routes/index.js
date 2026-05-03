const express = require('express');
const { checkout } = require('../controllers/checkoutController');
const { financialReport } = require('../controllers/reportController');
const { deleteUser } = require('../controllers/userController');

const router = express.Router();

router.post('/checkout', checkout);
router.get('/admin/financial-report', financialReport);
router.delete('/users/:id', deleteUser);

module.exports = router;
