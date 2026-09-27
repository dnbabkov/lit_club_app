import sqlite3

db_address = "/home/soberjan/PythonProjects/lit_club_app/tg_bot/database.db"

def create_db():
    con = sqlite3.connect(db_address)
    cur = con.cursor()

    cur.execute('CREATE TABLE votes(user_id, book, score)')
    con.commit()
    con.close()
    
def add_book(user_id, book, score, epoch):
    con = sqlite3.connect(db_address)
    cur = con.cursor()
    book = book.lower()
    cur.execute("INSERT INTO votes VALUES(?, ?, ?, ?)", (str(user_id), book, score, epoch))
    con.commit()
    con.close()
    return 'Ты добавил новую книгу'

def add_vote(user_id, book, score):
    if score < 0 or score > 5:
        return 'Оценка должна варьироваться от 1 до 5'
    
    con = sqlite3.connect(db_address)
    cur = con.cursor()

    book = book.lower()

    res = cur.execute("SELECT epoch FROM votes WHERE book = ?", (book, ))
    epoch = res.fetchone()
    if epoch == None:
        return 'Вы ввели несуществующую книгу'
    epoch = epoch[0]
    
    res = cur.execute("SELECT user_id, book FROM votes WHERE user_id=? AND book=?", (str(user_id), book, ))
    if len(res.fetchall()) == 0:
        cur.execute("INSERT INTO votes VALUES(?, ?, ?, ?)", (str(user_id), book, score, epoch))
    else:
        cur.execute("UPDATE votes SET score=? WHERE user_id=? AND book=?", (score, str(user_id), book, ))
    
    con.commit()
    con.close()

    return 'Ваш голос учтен :)'

def get_rating():
    con = sqlite3.connect(db_address)
    cur = con.cursor()

    res = cur.execute("SELECT book, AVG(score) avg_score, epoch FROM votes GROUP BY book ORDER BY avg_score DESC")
    return res.fetchall()

if __name__ == '__main__':
    rating = get_rating()
    # print(rating)
    # msg = ''
    # for book in rating:
    #     msg += str(book[0]) + ' ' + str(book[1]) + ' ' + book[2] + '\n'
    # print(msg)
    
    rating_dict = {}
    for r in rating:
        rating_dict[r[2]] = rating_dict.get(r[2], '') + r[0] + str(round(r[1], 2)) + '\n'
    res = ''
    for key, val in rating_dict.items():
        res += f"<b><u>{key}</u></b>\n" + val
    print(res)
