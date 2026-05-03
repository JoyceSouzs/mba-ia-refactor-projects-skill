const { getDb } = require('../database/connection');

async function getFinancialReport() {
    const db = await getDb();
    const courses = await db.all('SELECT * FROM courses');
    const report = [];

    for (const course of courses) {
        const enrollments = await db.all(
            'SELECT e.id, e.user_id FROM enrollments e WHERE e.course_id = ?',
            [course.id]
        );
        let revenue = 0;
        const students = [];

        for (const enr of enrollments) {
            const [user, payment] = await Promise.all([
                db.get('SELECT name, email FROM users WHERE id = ?', [enr.user_id]),
                db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enr.id]),
            ]);
            if (payment && payment.status === 'PAID') {
                revenue += payment.amount;
            }
            students.push({
                student: user ? user.name : 'Unknown',
                paid: payment ? payment.amount : 0,
            });
        }
        report.push({ course: course.title, revenue, students });
    }
    return report;
}

module.exports = { getFinancialReport };
