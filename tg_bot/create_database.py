import sqlite3

db_address = "database.db"

def create_db():
    con = sqlite3.connect(db_address)
    cur = con.cursor()

    cur.execute('CREATE TABLE votes(user_id, book, score)')
    con.commit()
    con.close()

def create_achievement_table():
    con = sqlite3.connect(db_address)
    cur = con.cursor()

    cur.execute('CREATE TABLE achievements(user_id, path)')
    con.commit()
    con.close()

# def create_users_table():
#     con = sqlite3.connect(db_address)
#     cur = con.cursor()

#     cur.execute('CREATE TABLE users(id, role, tg_id)')
#     con.commit()
#     con.close()

