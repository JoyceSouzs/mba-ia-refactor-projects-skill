const bcrypt = require('bcrypt');
const { getDb } = require('../database/connection');

const SALT_ROUNDS = 12;

async function findByEmail(email) {
    const db = await getDb();
    return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create(name, email, password) {
    const db = await getDb();
    const hash = await bcrypt.hash(password, SALT_ROUNDS);
    const result = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, hash]
    );
    return result.lastID;
}

async function deleteById(userId) {
    const db = await getDb();
    await db.run('BEGIN TRANSACTION');
    try {
        const enrollments = await db.all('SELECT id FROM enrollments WHERE user_id = ?', [userId]);
        for (const enr of enrollments) {
            await db.run('DELETE FROM payments WHERE enrollment_id = ?', [enr.id]);
        }
        await db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        await db.run('DELETE FROM users WHERE id = ?', [userId]);
        await db.run('COMMIT');
    } catch (err) {
        await db.run('ROLLBACK');
        throw err;
    }
}

module.exports = { findByEmail, create, deleteById };
