import sqlite3


db_address = "/home/soberjan/PythonProjects/lit_club_app/tg_bot/database.db"

def add_user(id, tg_id, role):
    if role != 'admin' and role != 'user':
        return 'Такой роли не существует'
    
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res = cur.execute('SELECT id FROM users WHERE id=?', (id,)).fetchone()
    if res != None:
        return 'Пользователь уже существует'

    cur.execute("INSERT INTO users VALUES(?, ?, ?)", (str(id), role, tg_id))
    con.commit()
    con.close()
    return 'Пользователь успешно добавлен'

def update_role(id, role):
    if role != 'admin' and role != 'user':
        return 'Такой роли не существует'
    
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res = cur.execute('SELECT id FROM users WHERE tg_id=?', (id,)).fetchone()
    if res == None:
        return 'Пользователя не существует'

    cur.execute("UPDATE users SET role = ? WHERE tg_id = ?", (role, id))
    con.commit()
    con.close()
    return 'Роль пользователя обновлена'

def get_users():
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res = cur.execute('SELECT id, tg_id, role FROM users').fetchall()
    con.close()
    return '\n'.join([str(id) + ' ' + str(tg_id) + ' ' + role for id, tg_id, role in res])

def get_all_tg_ids():
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res = cur.execute('SELECT tg_id FROM users').fetchall()
    con.close()
    return ' '.join([str(tg_id[0]) for tg_id in res])

def get_role(id):
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res = cur.execute('SELECT role FROM users WHERE id = ?', (str(id),)).fetchone()
    con.close()
    return res

def delete_user(tg_id):
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res =  cur.execute('SELECT role FROM users WHERE tg_id = ?', (tg_id,)).fetchone()
    if res == None:
        return 'Такого пользователя не существует'
    
    cur.execute('DELETE FROM users WHERE tg_id=?', (tg_id,))
    con.commit()
    con.close()
    return 'Пользователь успешно удален'

def update_tg_id(id, new_tg_id):
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    
    res =  cur.execute('SELECT role FROM users WHERE id = ?', (id,)).fetchone()
    if res == None:
        return 'Такого пользователя не существует'
    
    cur.execute("UPDATE users SET tg_id = ? WHERE id = ?", (new_tg_id, id))
    
    con.commit()
    con.close()
    return 'Айди пользователя успешно обновлен'
    

if __name__ == '__main__':
    print(get_all_tg_ids())
    print(delete_user('@asdf'))
