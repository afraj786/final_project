from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import pickle

app = Flask(__name__)
model = pickle.load(open('gradientboostmodel.pkl', 'rb'))

app.secret_key = 'xyzsdfg'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'user-system'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('home.html')





@app.route('/ownersignin')
def ownersignin():
    return render_template('ownersignin.html')


@app.route('/send', methods=['GET', 'POST'])
def ownersigin():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        hotel_name = request.form['hotel_name']
        hotel_timing = request.form['hotel_timing']
        city = request.form['city']
        region = request.form['region']
        cuisine_type = request.form['cuisine_type']
        cuisine_category = request.form['cuisine_category']

        # Save the data to the database
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO registration (name, email, phone, password, hotel_name, hotel_timing, city, region, cuisine_type, cuisine_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, password, hotel_name, hotel_timing, city, region, cuisine_type, cuisine_category))
        mysql.connection.commit()
        cur.close()

        # Redirect to the login page
        return redirect(url_for('ownerlogin'))

    # Render the registration form template
    return render_template('ownersignin.html')


@app.route('/ologin', methods=['GET', 'POST'])
def ownerlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the credentials exist in the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM registration WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            # User is authenticated, redirect to the dashboard or another page
            return render_template('ownerpage.html')
        else:
            # Invalid credentials, show an error message
            error = 'Invalid email or password'
            return render_template('ownerlogin.html', error=error)

    # Render the login page template
    return render_template('ownerlogin.html')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    # get the form data submitted by the user
    category = request.form.get('category')
    cuisine = request.form.get('cuisine')
    week = request.form.get('week')
    checkout_price = request.form.get('checkout_price')
    base_price = request.form.get('base_price')
    emailer = request.form.get('emailer')
    homepage = request.form.get('homepage')
    city = request.form.get('city')
    region = request.form.get('region')
    op_area = request.form.get('op_area')
    center_type = request.form.get('center_type')

    # check that all inputs are not empty strings
    if '' in [category, cuisine, week, checkout_price, base_price, emailer, homepage, city, region, op_area, center_type]:
        return render_template('index.html', error='All fields are required!')

    # convert inputs to the correct data types
    try:
        category = int(category)
        cuisine = int(cuisine)
        week = int(week)
        checkout_price = float(checkout_price)
        base_price = float(base_price)
        emailer = int(emailer)
        homepage = int(homepage)
        city = int(city)
        region = int(region)
        op_area = float(op_area)
        center_type = int(center_type)
    except ValueError:
        return render_template('index.html', error='Invalid input data type!')

    # make a prediction using the loaded model and the user inputs
    input_data = [[category, cuisine, week, checkout_price, base_price, emailer, homepage, city, region, op_area, center_type]]
    prediction = model.predict(input_data)[0]

    # return the predicted value to the user
    return render_template('index.html', prediction=prediction)



@app.route('/submit', methods=['GET', 'POST'])
def feedbackform():
    if request.method == 'POST':
        # Fetch form data
        name = request.form['name']
        email = request.form['email']
        ratings = request.form['ratings']
        feedback = request.form['feedback']

        # Create cursor
        cur = mysql.connection.cursor()

        # Insert data into the database
        cur.execute("INSERT INTO feedback (name, email, ratings, feedback) VALUES (%s, %s, %s, %s)",
                    (name, email, ratings, feedback))

        # Commit to the database
        mysql.connection.commit()

        # Close cursor
        cur.close()

        return render_template('home.html')

    return render_template('feedbackform.html')


@app.route('/ownerpage')
def ownerpage():
    return render_template('ownerpage.html')


@app.route('/customerpage')
def customerpage():
    return render_template('customerpage.html')


@app.route('/customersignin')
def customersignin():
    return render_template('customersignin.html')



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        region = request.form['region']
        cuisine_type = request.form['cuisine_type']
        rating = float(request.form['rating'])
        # Additional filtering criteria like price can be included as well

        # Execute the SQL query to retrieve restaurant data
        query = """
             SELECT city, region, category, cuisine_type, rating, price, hotel_name
             FROM zomatodata
             WHERE region = %s AND cuisine_type = %s AND rating >= %s
             ORDER BY rating DESC
             LIMIT 5;
        """
        cursor = mysql.connection.cursor()
        cursor.execute(query, (region, cuisine_type, rating))
        results = cursor.fetchall()
        cursor.close()

        return render_template('results.html', results=results, region=region)

    return render_template('search.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM uspage WHERE email = %s AND password = %s', (email, password,))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return render_template('customerpage.html', message=message)
        else:
            message = 'Please enter correct email / password!'
    return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM uspage WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO uspage VALUES (NULL, %s, %s, %s)', (userName, email, password,))
            mysql.connection.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)
