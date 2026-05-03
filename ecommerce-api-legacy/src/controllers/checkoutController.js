const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const settings = require('../config/settings');

function validateCheckoutInput({ userName, email, courseId, cardNumber }) {
    if (!userName || !email || !courseId || !cardNumber) {
        return 'userName, email, courseId e cardNumber são obrigatórios';
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return 'Email inválido';
    }
    if (!Number.isInteger(Number(courseId))) {
        return 'courseId deve ser um número inteiro';
    }
    if (typeof cardNumber !== 'string' || cardNumber.length < 13) {
        return 'Número de cartão inválido';
    }
    return null;
}

function processCard(cardNumber) {
    // Simplified simulator: cards starting with 4 = VISA approved, others = denied
    return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

async function checkout(req, res, next) {
    try {
        const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
        const validationError = validateCheckoutInput({ userName, email, courseId, cardNumber });
        if (validationError) {
            return res.status(400).json({ error: validationError });
        }

        const course = await courseModel.findActiveById(courseId);
        if (!course) {
            return res.status(404).json({ error: 'Curso não encontrado ou inativo' });
        }

        let user = await userModel.findByEmail(email);
        if (!user) {
            const userId = await userModel.create(userName, email, password || '123456');
            user = { id: userId };
        }

        const paymentStatus = processCard(cardNumber);
        if (paymentStatus === 'DENIED') {
            return res.status(400).json({ error: 'Pagamento recusado' });
        }

        console.log(`[INFO] Processando cartão via gateway ${settings.paymentGatewayKey.substring(0, 7)}***`);

        const enrollmentId = await courseModel.createEnrollment(user.id, courseId);
        await courseModel.createPayment(enrollmentId, course.price, paymentStatus);
        await courseModel.logAudit(`Checkout curso ${courseId} por usuario ${user.id}`);

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
