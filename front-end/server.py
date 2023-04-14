import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from flask import Flask, request, render_template, g, redirect, Response, flash, url_for, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'your_secret_key'

DATABASEURI = f"postgresql://yw3945:1885@34.28.53.86/project1"

engine = create_engine(DATABASEURI)
metadata = MetaData()

account_table = Table('ACCOUNT', metadata)
metadata.reflect(bind=engine)

category_table = Table('CATEGORY', metadata)
product_table = Table('PRODUCT', metadata)

@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html', logged_in=True)
    else:
        return render_template('index.html', logged_in=False)

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        address = request.form['address']
        states = request.form['states']
        email = request.form['email']

        insert_stmt = account_table.insert().values(
            user_id=user_id,
            name=name,
            address=address,
            states=states,
            email=email,
            searching_history=''
        )
        g.conn.execute(insert_stmt)
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        query = "SELECT * FROM ACCOUNT WHERE user_id = :user_id"
        user = g.conn.execute(text(query), user_id=user_id).fetchone()

        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('index'))
        else:
            flash('Incorrect user ID, please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Search products
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        search_query = request.form['search_query']
        query = "SELECT * FROM PRODUCT WHERE name ILIKE :search_query OR description ILIKE :search_query"
        search_results = g.conn.execute(text(query), search_query=f'%{search_query}%').fetchall()

        return render_template('search_results.html', search_results=search_results)
    else:
        return render_template('search.html')

# Add a new product
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']

        description = request.form['description']
        price = request.form['price']

        query = "INSERT INTO PRODUCT (name, description, price) VALUES (:name, :description, :price)"
        g.conn.execute(text(query), name=name, description=description, price=price)

        flash('Product added successfully')
        return redirect(url_for('add_product'))
    else:
        return render_template('add_product.html')


if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8112, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
