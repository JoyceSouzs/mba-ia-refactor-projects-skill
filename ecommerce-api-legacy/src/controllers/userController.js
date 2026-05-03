const userModel = require('../models/userModel');

async function deleteUser(req, res, next) {
    try {
        const userId = parseInt(req.params.id, 10);
        if (!userId || isNaN(userId)) {
            return res.status(400).json({ error: 'ID de usuário inválido' });
        }
        await userModel.deleteById(userId);
        return res.json({ message: 'Usuário e dados associados removidos com sucesso' });
    } catch (err) {
        next(err);
    }
}

module.exports = { deleteUser };
