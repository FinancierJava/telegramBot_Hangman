import sqlite3
from typing import List, Optional, Tuple

# Establish a database connection
conn = sqlite3.connect('hangman.db')
cursor = conn.cursor()

# Create the scores table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS scores (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT,
    score INTEGER,
    player_words TEXT  -- New column to store player words
)
''')
conn.commit()


async def add_chat_id_if_not_exists(player_id: int) -> None:
    cursor.execute('SELECT player_id FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute('INSERT INTO scores (player_id, player_name, score, player_words) VALUES (?, ?, ?, ?)',
                       (player_id, "", 0, ""))
        conn.commit()


async def save_score(player_id: int, player_name: str, points: int) -> None:
    cursor.execute('SELECT score FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()

    if row:
        current_score = row[0]
        new_score = current_score + points
        cursor.execute('UPDATE scores SET score = ? WHERE player_id = ?', (new_score, player_id))
    else:
        cursor.execute('INSERT INTO scores (player_id, player_name, score, player_words) VALUES (?, ?, ?, ?)',
                       (player_id, player_name, points, ''))

    conn.commit()


async def get_score(player_id: int) -> Optional[int]:
    cursor.execute('SELECT score FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()
    return row[0] if row else None


async def get_top_scores(limit: int = 10) -> List[Tuple[str, int]]:
    cursor.execute('SELECT player_name, score FROM scores ORDER BY score DESC LIMIT ?', (limit,))
    return cursor.fetchall()


async def save_word(player_id: int, word: str) -> int:
    cursor.execute('SELECT player_words FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()

    if row:
        current_words = row[0]
        if current_words:
            word_list = current_words.split(', ')
            if word in word_list:
                return 0  # Word already exists, return 0
            new_words = f"{current_words}, {word}"
        else:
            new_words = word
        cursor.execute('UPDATE scores SET player_words = ? WHERE player_id = ?', (new_words, player_id))
    else:
        cursor.execute('INSERT INTO scores (player_id, player_words) VALUES (?, ?)', (player_id, word))

    conn.commit()
    return 1  # Successfully added the word, return 1


async def get_player_words(player_id: int) -> Optional[str]:
    cursor.execute('SELECT player_words FROM scores WHERE player_id = ?', (player_id,))
    row = cursor.fetchone()
    return row[0] if row else None
