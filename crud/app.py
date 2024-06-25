from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import pymysql.cursors, os, re
from datetime import datetime

application = Flask(__name__)
application.secret_key = 'your_secret_key'

conn = cursor = None

@application.template_filter('datetimeformat')
def datetime_format(value, format_str):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return ''
    return value.strftime(format_str)

# Open database connection
def openDb():
    global conn, cursor
    try:
        conn = pymysql.connect(db="db_perpus", user="root", passwd="", host="localhost", port=3306, autocommit=True)
        cursor = conn.cursor()
    except Exception as e:
        print("Error:", e)
        return None
    return conn

# Close database connection
def closeDb():
    global conn, cursor
    cursor.close()
    conn.close()

# Home route
@application.route('/')
def home():
    return render_template('login.html')

# Login route
@application.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    openDb()
    cursor.execute("SELECT * FROM user WHERE nama=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    closeDb()
    if user:
        return redirect(url_for('books'))
    else:
        flash('Invalid credentials, please try again.')
        return redirect(url_for('home'))

# Register route
@application.route('/register', methods=['POST'])
def register():
    user_id = request.form['nik']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    openDb()
    cursor.execute("SELECT * FROM user WHERE nama=%s AND nik=%s", (username, user_id))
    user = cursor.fetchone()
    if user:
        flash('User already exists.')
        closeDb()
        return redirect(url_for('home'))
    else:
        cursor.execute("INSERT INTO user (nik, nama, email, password) VALUES (%s, %s, %s, %s)", (user_id, username, email, password))
        conn.commit()
        closeDb()
        return redirect(url_for('books'))

# Books route (view books)
@application.route('/books')
def books():
    openDb()
    container = []
    sql = "SELECT * FROM buku ORDER BY id DESC;"
    cursor.execute(sql)
    results = cursor.fetchall()
    for data in results:
        container.append(data)
    closeDb()
    print(container)
    return render_template('books.html', container=container)

# Generate unique book ID
def generate_book_id():
    openDb()
    cursor.execute("SELECT id FROM buku ORDER BY id DESC LIMIT 1")
    last_id = cursor.fetchone()
    closeDb()
    if last_id:
        last_id_num = None
        try:
            last_id_num = int(last_id[0][2:])
        except ValueError:
            pass
        if last_id_num is not None:
            new_id = f"BU{str(last_id_num + 1).zfill(4)}"
        else:
            new_id = "BU0001"
    else:
        new_id = "BU0001"
    return new_id

# Add book route
@application.route('/add_book', methods=['GET', 'POST'])
def add_book():
    generated_book_id = generate_book_id()
    if request.method == 'POST':
        book_id = request.form['id']
        title = request.form['judul']
        author = request.form['penulis']
        publisher = request.form['penerbit']
        year = request.form['tahun']
        stocks = request.form['stok']
        # Handle image upload
        cover_filename = 'book.jpeg'  # Default image
        if 'foto' in request.files:
            cover = request.files['foto']
            if cover.filename != '':
                cover_filename = f"{book_id}.jpg"
                cover_path = os.path.join(application.config['UPLOAD_FOLDER'], cover_filename)
                if os.path.exists(cover_path):
                    os.remove(cover_path)
                cover.save(cover_path)
        openDb()
        sql = "INSERT INTO buku (id, judul, penulis, penerbit, tahun, stok, cover) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (book_id, title, author, publisher, year, stocks, cover_filename)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('books'))
    else:
        return render_template('addbook.html', book_id=generated_book_id)
    
# Edit book route
@application.route('/edit_book/<id>', methods=['GET', 'POST'])
def edit_book(id):
    openDb()
    cursor.execute('SELECT * FROM buku WHERE id=%s', (id,))
    data = cursor.fetchone()
    openDb()
    if request.method == 'POST':
        book_id = request.form['id']
        title = request.form['judul']
        author = request.form['penulis']
        publisher = request.form['penerbit']
        year = request.form['tahun']
        stocks = request.form['stok']
        # Handle image upload
        cover_filename = 'book.jpeg'  # Default image
        if 'foto' in request.files:
            cover = request.files['foto']
            if cover.filename != '':
                cover_filename = f"{book_id}.jpg"
                cover_path = os.path.join(application.config['UPLOAD_FOLDER'], cover_filename)
                if os.path.exists(cover_path):
                    os.remove(cover_path)
                cover.save(cover_path)
        sql = "UPDATE buku SET judul=%s, penulis=%s, penerbit=%s, tahun=%s, stok=%s, cover=%s WHERE id=%s"
        val = (title, author, publisher, year, stocks, cover_filename, book_id)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('books'))
    else:
        # Add the logic to fetch book data for editing
        return render_template('editbook.html', data=data)
    
# Delete book route
@application.route('/delete_book/<id>', methods=['GET', 'POST'])
def delete_book(id):
    openDb()
    cursor.execute('DELETE FROM buku WHERE id=%s', (id,)) 
    path_to_photo = os.path.join(application.root_path, 'static/foto', f'{id}.jpg')
    if os.path.exists(path_to_photo):
        os.remove(path_to_photo)
    conn.commit()
    closeDb()
    return redirect(url_for('books'))

# Users route (view users)
@application.route('/members')
def members():
    openDb()
    container = []
    sql = "SELECT * FROM user ORDER BY nik DESC;"
    cursor.execute(sql)
    results = cursor.fetchall()
    for data in results:
        container.append(data)
    closeDb()
    print(container)
    return render_template('members.html', container=container)

# Generate unique user ID
def generate_user_id():
    openDb()
    cursor.execute("SELECT nik FROM user ORDER BY nik DESC LIMIT 1")
    last_id = cursor.fetchone()
    closeDb()
    if last_id:
        last_id_num = int(last_id[0][2:])
        new_id = f"AN{str(last_id_num + 1).zfill(4)}"
    else:
        new_id = "AN0001"
    return new_id

# Add user route
@application.route('/add_user', methods=['GET', 'POST'])
def add_user():
    generated_user_id = generate_user_id()
    if request.method == 'POST':
        user_id = request.form['nik']
        name = request.form['nama']
        email = request.form['email']
        gender = request.form['jenis_kelamin']
        birthdate = request.form['tanggal_lahir']
        address = request.form['alamat']
        password = request.form['password']        
        photo_filename = 'user.jpg'  # Default image
        if 'foto' in request.files:
            photo = request.files['foto']
            if photo.filename != '':
                photo_filename = f"{user_id}.jpg"
                photo_path = os.path.join(application.config['UPLOAD_FOLDER'], photo_filename)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                photo.save(photo_path)
        openDb()
        sql = "INSERT INTO user (nik, nama, email, jenis_kelamin, tanggal_lahir, alamat, password, foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (user_id, name, email, gender, birthdate, address, password, photo_filename)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('members'))
    else:
        return render_template('adduser.html', user_id=generated_user_id)
    
# Edit user route
@application.route('/edit_user/<nik>', methods=['GET', 'POST'])
def edit_user(nik):
    openDb()
    cursor.execute('SELECT * FROM user WHERE nik=%s', (nik,))
    data = cursor.fetchone()
    if request.method == 'POST':
        user_id = request.form['nik']
        name = request.form['nama']
        email = request.form['email']
        gender = request.form['jenis_kelamin']
        birthdate = request.form['tanggal_lahir']
        address = request.form['alamat']
        password = request.form['password']  # Consider hashing the password
        # Handle photo upload
        photo_filename = 'user.jpg'
        if 'foto' in request.files:
            photo = request.files['foto']
            if photo.filename != '':
                photo_filename = f"{user_id}.jpg"
                photo_path = os.path.join(application.config['UPLOAD_FOLDER'], photo_filename)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                photo.save(photo_path)
        # Update user data in the database
        sql = """
            UPDATE user 
            SET nama=%s, email=%s, jenis_kelamin=%s, tanggal_lahir=%s, alamat=%s, password=%s, foto=%s 
            WHERE nik=%s
        """
        val = (name, email, gender, birthdate, address, password, photo_filename, user_id)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('members'))
    else:
        closeDb()
        return render_template('edituser.html', data=data)

# Delete user route
@application.route('/delete_user/<nik>', methods=['GET', 'POST'])
def delete_user(nik):
    openDb()
    cursor.execute('DELETE FROM user WHERE nik=%s', (nik,)) 
    path_to_photo = os.path.join(application.root_path, 'static/foto', f'{nik}.jpg')
    if os.path.exists(path_to_photo):
        os.remove(path_to_photo)
    conn.commit()
    closeDb()
    return redirect(url_for('members'))

# Photo upload folder
UPLOAD_FOLDER = '/web_perpus/crud/static/foto/'
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# PDF print route
@application.route('/get_student_data/<nik>', methods=['GET'])
def get_student_data(nik):
    connection = pymysql.connect(host='localhost', user='root', password='', db='db_perpus', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM user WHERE nik = %s"
            cursor.execute(sql, (nik,))
            student_data = cursor.fetchone()
            print("Menerima permintaan untuk NIK:", nik)
            print("Data yang dikirim:", student_data)
            return jsonify(student_data)
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Terjadi kesalahan saat mengambil data'}), 500
    finally:
        connection.close()

@application.route('/transactions')
def transactions():
    openDb()
    sql = "SELECT * FROM transaksi"
    cursor.execute(sql)
    results = cursor.fetchall()
    closeDb()
    # Render the template with the fetched data
    return render_template('transactions.html', container=results)

# Function to generate unique loan ID
def generate_loan_id():
    openDb()
    cursor.execute("SELECT np FROM transaksi ORDER BY np DESC LIMIT 1")
    last_id = cursor.fetchone()
    closeDb()
    if last_id:
        last_id_num = int(last_id[0][2:]) 
        new_id = f"PJ{str(last_id_num + 1).zfill(4)}"
    else:
        new_id = "PJ0001"
    return new_id

# Add loans for transaction data
@application.route('/add_loans', methods=['GET', 'POST'])
def add_loans():
    generated_loan_id = generate_loan_id()
    if request.method == 'POST':
        user_id = request.form['nik']
        book_id = request.form['id']
        loan_date = request.form['tanggal_peminjaman']
        due_date = request.form['tanggal_jatuh_tempo']
        return_date = request.form.get('tanggal_pengembalian', None)  # Optional return date
        penalty = request.form.get('denda', 0)  # Default to 0 if not provided
        openDb()
        if conn is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500
        sql = """INSERT INTO transaksi (np, nik, id, tanggal_peminjaman, tanggal_jatuh_tempo, tanggal_pengembalian, denda) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        val = (generated_loan_id, user_id, book_id, loan_date, due_date, return_date, penalty)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        decrease_stock(book_id)
        return redirect(url_for('transactions'))
    else:
        return render_template('addloans.html', loan_id=generated_loan_id)

# Update returns for transaction data
@application.route('/edit_returns/<np>/<id>', methods=['GET', 'POST'])
def edit_returns(np, id):
    openDb()
    cursor.execute('SELECT * FROM transaksi WHERE np=%s AND id=%s', (np, id))
    data = cursor.fetchone()
    if request.method == 'POST':
        loan_id = request.form['np']
        user_id = request.form['nik']
        book_id = request.form['id']
        loan_date = request.form['tanggal_peminjaman']
        due_date = request.form['tanggal_jatuh_tempo']
        return_date = request.form['tanggal_pengembalian']
        penalty = request.form.get('denda', 0)  # Default to 0 if not provided
        cursor.execute("""
            UPDATE transaksi
            SET nik = %s, id = %s, tanggal_peminjaman = %s, tanggal_jatuh_tempo = %s,
            tanggal_pengembalian = %s, denda = %s
            WHERE np = %s
        """, (user_id, book_id, loan_date, due_date, return_date, penalty, loan_id))
        conn.commit()
        closeDb()
        increase_stock(book_id)  # Assuming loan_id is the book_id here
        return redirect(url_for('transactions'))
    else:
        closeDb()
        return render_template('editreturns.html', data=data)

# Delete transaction route
@application.route('/delete_transaction/<np>', methods=['GET', 'POST'])
def delete_transaction(np):
    openDb()
    cursor.execute('DELETE FROM transaksi WHERE np=%s', (np,))
    conn.commit()
    closeDb()
    return redirect(url_for('transactions'))

# Helper function to decrease stock
def decrease_stock(book_id):
    openDb()
    cursor.execute('UPDATE buku SET stok = stok - 1 WHERE id = %s AND stok > 0', (book_id))
    conn.commit()
    closeDb()

# Helper function to increase stock
def increase_stock(book_id):
    openDb()
    cursor.execute('UPDATE buku SET stok = stok + 1 WHERE id = %s AND stok > 0', (book_id))
    conn.commit()
    closeDb()

# Main function
if __name__ == '__main__':
    application.run(debug=True)