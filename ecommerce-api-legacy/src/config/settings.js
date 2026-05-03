require('dotenv').config();

const settings = {
    port: parseInt(process.env.PORT || '3000', 10),
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_placeholder',
    smtpUser: process.env.SMTP_USER || '',
    smtpPass: process.env.SMTP_PASS || '',
    dbUser: process.env.DB_USER || 'admin',
    dbPass: process.env.DB_PASS || '',
};

module.exports = settings;
