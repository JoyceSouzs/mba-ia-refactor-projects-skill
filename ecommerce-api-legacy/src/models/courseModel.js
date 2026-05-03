const { getDb } = require('../database/connection');

async function findActiveById(courseId) {
    const db = await getDb();
    return db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [courseId]);
}

async function createEnrollment(userId, courseId) {
    const db = await getDb();
    const result = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId]
    );
    return result.lastID;
}

async function createPayment(enrollmentId, amount, status) {
    const db = await getDb();
    const result = await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return result.lastID;
}

async function logAudit(action) {
    const db = await getDb();
    await db.run(
        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [action]
    );
}

module.exports = { findActiveById, createEnrollment, createPayment, logAudit };
