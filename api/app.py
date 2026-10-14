from flask import Flask, jsonify, request 
import psycopg2 
import redis 
import os 
import json 
 
app = Flask(__name__) 
 
# Конфигурация из env vars 
DB_CONFIG = { 
    "host": os.environ["DB_HOST"], 
    "port": os.environ["DB_PORT"], 
    "database": os.environ["DB_NAME"], 
    "user": os.environ["DB_USER"], 
    "password": os.environ["DB_PASSWORD"] 
} 
 
REDIS_HOST = os.environ["REDIS_HOST"] 
REDIS_PORT = int(os.environ["REDIS_PORT"]) 
 
# Redis client 
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, 
decode_responses=True) 
 
@app.route("/") 
def home(): 
    return jsonify({ 
        "app": "Lab5 API", 
        "status": "running" 
    }) 
 
@app.route("/health") 
def health(): 
    return jsonify({"status": "healthy"})
@app.route("/db-test") 
def db_test(): 
    try: 
        conn = psycopg2.connect(**DB_CONFIG) 
        cur = conn.cursor() 
        cur.execute("SELECT version();") 
        version = cur.fetchone()[0] 
        cur.close() 
        conn.close() 
        return jsonify({"status": "success", "database": version}) 
    except Exception as e: 
        return jsonify({"status": "error", "error": str(e)}), 500 
 
@app.route("/cache-test") 
def cache_test(): 
    try: 
        redis_client.set("test_key", "test_value", ex=60) 
        value = redis_client.get("test_key") 
        return jsonify({"status": "success", "redis": "connected", "test_value": 
value}) 
    except Exception as e: 
        return jsonify({"status": "error", "error": str(e)}), 500 

def get_db_connection():
    """Establish connection to PostgreSQL and ensure the users table exists."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            );
        """)
        conn.commit()
    return conn

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email;",
            (name, email)
        )
        new_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        user_data = {"id": new_user[0], "name": new_user[1], "email": new_user[2]}
        redis_client.set(f"user:{new_user[0]}", json.dumps(user_data), ex=60)

        return jsonify(user_data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/users", methods=["GET"])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = [{"id": row[0], "name": row[1], "email": row[2]} for row in rows]
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    cache_key = f"user:{user_id}"

    # 1. Check Redis cache first
    cached_user = redis_client.get(cache_key)
    if cached_user:
        return jsonify({"source": "cache", "data": json.loads(cached_user)})

    # 2. Query database if not in cache
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({"error": "User not found"}), 404

        user_data = {"id": row[0], "name": row[1], "email": row[2]}
        redis_client.setex(cache_key, 60, json.dumps(user_data))

        return jsonify({"source": "database", "data": user_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000) 
