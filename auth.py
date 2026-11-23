
import sqlite3
import hashlib
import secrets
import hmac

DB_NAME = "chatbot.db"


# ==================================================
# 1. DATABASE INITIALIZATION
# ==================================================

def init_db():

    connection = sqlite3.connect(DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")

    # Users table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Conversations table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # Messages table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


# ==================================================
# 2. PASSWORD HASHING
# ==================================================

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    ).hex()

    return salt, password_hash


# ==================================================
# 3. USER SIGNUP
# ==================================================

def signup(username, password):

    username = username.strip()

    if not username or not password:
        return False, "Username and password are required."

    salt, password_hash = hash_password(password)

    try:

        connection = sqlite3.connect(DB_NAME)

        connection.execute(
            """
            INSERT INTO users (username, salt, password_hash)
            VALUES (?, ?, ?)
            """,
            (username, salt, password_hash)
        )

        connection.commit()
        connection.close()

        return True, "Account created successfully!"

    except sqlite3.IntegrityError:
        return False, "Username already exists."

    except sqlite3.Error:
        return False, "Database error occurred."


# ==================================================
# 4. USER LOGIN
# ==================================================

def login(username, password):

    connection = sqlite3.connect(DB_NAME)

    user = connection.execute(
        "SELECT salt, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()

    connection.close()

    if user is None:
        return False

    salt, stored_hash = user

    _, entered_hash = hash_password(password, salt)

    return hmac.compare_digest(stored_hash, entered_hash)


# ==================================================
# 5. GET USER ID
# ==================================================

def get_user_id(username):

    connection = sqlite3.connect(DB_NAME)

    user = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()

    connection.close()

    return user[0] if user else None


# ==================================================
# 6. CREATE NEW CHAT
# ==================================================

def create_chat(user_id, title="New Chat"):

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        """
        INSERT INTO chats (user_id, title)
        VALUES (?, ?)
        """,
        (user_id, title)
    )

    chat_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return chat_id


# ==================================================
# 7. SAVE MESSAGE
# ==================================================

def save_message(chat_id, role, content):

    connection = sqlite3.connect(DB_NAME)

    connection.execute(
        """
        INSERT INTO messages (chat_id, role, content)
        VALUES (?, ?, ?)
        """,
        (chat_id, role, content)
    )

    connection.commit()
    connection.close()


# ==================================================
# 8. GET USER'S CHAT HISTORY
# ==================================================

def get_user_chats(user_id):

    connection = sqlite3.connect(DB_NAME)

    chats = connection.execute(
        """
        SELECT id, title, created_at
        FROM chats
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return chats


# ==================================================
# 9. GET MESSAGES FROM A CHAT
# ==================================================

def get_chat_messages(chat_id, user_id):

    connection = sqlite3.connect(DB_NAME)

    messages = connection.execute(
        """
        SELECT messages.role, messages.content
        FROM messages
        JOIN chats ON messages.chat_id = chats.id
        WHERE messages.chat_id = ?
        AND chats.user_id = ?
        ORDER BY messages.id ASC
        """,
        (chat_id, user_id)
    ).fetchall()

    connection.close()

    return [
        {"role": role, "content": content}
        for role, content in messages
    ]


# ==================================================
# 10. RENAME CHAT
# ==================================================

def rename_chat(chat_id, user_id, new_title):

    new_title = new_title.strip()

    if not new_title:
        return False

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        """
        UPDATE chats
        SET title = ?
        WHERE id = ? AND user_id = ?
        """,
        (new_title, chat_id, user_id)
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


# ==================================================
# 11. DELETE CHAT
# ==================================================

def delete_chat(chat_id, user_id):

    connection = sqlite3.connect(DB_NAME)

    # Enable foreign key cascading for this connection
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.execute(
        """
        DELETE FROM chats
        WHERE id = ? AND user_id = ?
        """,
        (chat_id, user_id)
    )

    connection.commit()

    deleted = cursor.rowcount > 0

    connection.close()

    return deleted
