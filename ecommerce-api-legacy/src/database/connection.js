const sqlite3 = require('sqlite3');
const { open } = require('sqlite');

let _db = null;

async function getDb() {
    if (_db) return _db;
    _db = await open({ filename: ':memory:', driver: sqlite3.Database });
    await _initSchema(_db);
    return _db;
}

async function _initSchema(db) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            pass TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            created_at DATETIME DEFAULT (datetime('now'))
        );
    `);

    const count = await db.get('SELECT COUNT(*) as n FROM courses');
    if (count.n === 0) {
        await db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '$2b$12$placeholder_hash')");
        await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
        await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
    }
}

module.exports = { getDb };
