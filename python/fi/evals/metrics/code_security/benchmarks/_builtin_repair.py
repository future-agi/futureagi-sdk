"""Repair for builtin."""
from __future__ import annotations

from fi.evals.metrics.code_security.benchmarks.builtin import (RepairTest)

PYTHON_REPAIR_TESTS = [
    RepairTest(
        id="py-repair-sql-001",
        vulnerable_code='''
def get_user(conn, name):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
''',
        language="python",
        cwes_to_fix=["CWE-89"],
        fixed_reference='''
def get_user(conn, name):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    return cursor.fetchone()
''',
        fix_description="SQL injection vulnerability - use parameterized queries",
        tags=["sql", "injection"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-sql-002",
        vulnerable_code='''
def delete_user(conn, user_id):
    sql = "DELETE FROM users WHERE id = " + str(user_id)
    conn.execute(sql)
    conn.commit()
''',
        language="python",
        cwes_to_fix=["CWE-89"],
        fixed_reference='''
def delete_user(conn, user_id):
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
''',
        fix_description="SQL injection via string concatenation",
        tags=["sql", "injection"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-cmd-001",
        vulnerable_code='''
import os

def ping(hostname):
    os.system(f"ping -c 1 {hostname}")
''',
        language="python",
        cwes_to_fix=["CWE-78"],
        fixed_reference='''
import subprocess

def ping(hostname):
    subprocess.run(["ping", "-c", "1", hostname], capture_output=True)
''',
        fix_description="Command injection via os.system with user input",
        tags=["command", "injection"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-cmd-002",
        vulnerable_code='''
import subprocess

def run_command(user_cmd):
    subprocess.run(user_cmd, shell=True)
''',
        language="python",
        cwes_to_fix=["CWE-78"],
        fixed_reference='''
import subprocess
import shlex

def run_command(user_cmd):
    # Validate and sanitize the command
    allowed_commands = ['ls', 'pwd', 'date']
    parts = shlex.split(user_cmd)
    if parts and parts[0] in allowed_commands:
        subprocess.run(parts)
    else:
        raise ValueError("Command not allowed")
''',
        fix_description="Command injection via shell=True",
        tags=["command", "injection"],
        difficulty="medium",
    ),
    RepairTest(
        id="py-repair-crypto-001",
        vulnerable_code='''
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
''',
        language="python",
        cwes_to_fix=["CWE-327"],
        fixed_reference='''
import hashlib
import os

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + key
''',
        fix_description="Weak MD5 hash for password storage",
        tags=["crypto", "hashing"],
        difficulty="medium",
    ),
    RepairTest(
        id="py-repair-random-001",
        vulnerable_code='''
import random
import string

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
''',
        language="python",
        cwes_to_fix=["CWE-330"],
        fixed_reference='''
import secrets

def generate_token():
    return secrets.token_urlsafe(32)
''',
        fix_description="Insecure random for security token",
        tags=["crypto", "random"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-deser-001",
        vulnerable_code='''
import pickle

def load_data(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)
''',
        language="python",
        cwes_to_fix=["CWE-502"],
        fixed_reference='''
import json

def load_data(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
''',
        fix_description="Unsafe pickle deserialization",
        tags=["deserialization"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-yaml-001",
        vulnerable_code='''
import yaml

def load_config(filepath):
    with open(filepath) as f:
        return yaml.load(f)
''',
        language="python",
        cwes_to_fix=["CWE-502"],
        fixed_reference='''
import yaml

def load_config(filepath):
    with open(filepath) as f:
        return yaml.safe_load(f)
''',
        fix_description="Unsafe YAML loading",
        tags=["deserialization", "yaml"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-path-001",
        vulnerable_code='''
from flask import Flask, request, send_file

app = Flask(__name__)

@app.route('/download')
def download():
    filename = request.args.get('file')
    return send_file(f'/uploads/{filename}')
''',
        language="python",
        cwes_to_fix=["CWE-22"],
        fixed_reference='''
from flask import Flask, request, send_file, abort
from werkzeug.utils import safe_join
import os

app = Flask(__name__)
UPLOAD_DIR = '/uploads'

@app.route('/download')
def download():
    filename = request.args.get('file')
    if not filename:
        abort(400)
    filepath = safe_join(UPLOAD_DIR, filename)
    if not filepath or not os.path.exists(filepath):
        abort(404)
    return send_file(filepath)
''',
        fix_description="Path traversal vulnerability",
        tags=["path", "traversal"],
        difficulty="medium",
    ),
    RepairTest(
        id="py-repair-secrets-001",
        vulnerable_code='''
import boto3

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
        aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    )
''',
        language="python",
        cwes_to_fix=["CWE-798"],
        fixed_reference='''
import boto3
import os

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
''',
        fix_description="Hardcoded AWS credentials",
        tags=["secrets", "credentials"],
        difficulty="easy",
    ),
    RepairTest(
        id="py-repair-eval-001",
        vulnerable_code='''
def calculate(expression):
    return eval(expression)
''',
        language="python",
        cwes_to_fix=["CWE-94"],
        fixed_reference='''
import ast
import operator

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def calculate(expression):
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            return OPERATORS[type(node.op)](left, right)
        else:
            raise ValueError("Unsupported operation")

    tree = ast.parse(expression, mode='eval')
    return eval_node(tree.body)
''',
        fix_description="Code injection via eval",
        tags=["code", "injection"],
        difficulty="hard",
    ),
    RepairTest(
        id="py-repair-xss-001",
        vulnerable_code='''
from flask import Flask, request

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    return f'<h1>Search results for: {query}</h1>'
''',
        language="python",
        cwes_to_fix=["CWE-79"],
        fixed_reference='''
from flask import Flask, request
from markupsafe import escape

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    return f'<h1>Search results for: {escape(query)}</h1>'
''',
        fix_description="XSS via unescaped user input in HTML",
        tags=["xss", "injection"],
        difficulty="easy",
    ),
]
