from flask import Flask, render_template, redirect, request , url_for, jsonify, flash , session, logging
from flask.wrappers import Request
#from .data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.secret_key  = "SkillChen_Secret_KEY"
# Config MySQL 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'F9n3v47t'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Init MySQL
mysql = MySQL(app)



#Articles = Articles()

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get article
    result = cur.execute("select * from articles order by create_date desc")
    articles = cur.fetchall()
    if result > 0:
        return render_template("articles.html", articles=articles)
    else:
        msg = "No Articles Found!"
    return render_template('articles.html', msg=msg)
    # Close Connection 
    cur.close()

@app.route("/article/<string:id>/")
def article(id):
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get article
    result = cur.execute("select * from articles where id = %s", [id])
    article = cur.fetchone()
    return render_template("article.html",article=article)


class RegisterForm(Form):
    name = StringField(u'姓名(Name)', validators=[validators.Length(min=1, max=50)])
    username = StringField(u'使用者名稱(User Name)', validators=[validators.Length(min=4, max=25)])
    email = StringField(u'電子郵件(Email)', validators=[validators.Length(min=6, max=50)])
    password = PasswordField(u'密碼(Password)', validators=[
        validators.DataRequired(),
        validators.EqualTo(u'confirm', message='Password do not match!')
        ])
    confirm = PasswordField(u'確認密碼(Confirm Password)')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data 
        email = form.email.data 
        username = form.username.data 
        password = sha256_crypt.encrypt(str(form.password.data))
        # Create Cursor 
        cur = mysql.connection.cursor()
        # Execute SQL Command
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name,email,username,password))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        flash("You are now registered and can log in", 'success')       
        return redirect(url_for('login'))      
    return render_template('register.html',form=form)

# User Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor 
        cur = mysql.connection.cursor()
        # Get User by username
        result = cur.execute("SELECT * FROM users where username=%s",[username])
        if result > 0:
            # Get stored hash 
            data = cur.fetchone()
            password = data['password']
            # Compare Password 
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = username 
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login!!'
                return render_template('login.html', error=error)
            # Close Connection    
            cur.close()
        else:
            error = 'Username not found !!'
            return render_template('login.html', error=error)
       

    return render_template("login.html")

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session :
            return f(*args, **kwargs)
        else:
            flash('未經授權，請登錄 (Unauthorized, Please Login)', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

@app.route("/dashboard")
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get article
    result = cur.execute("select * from articles order by create_date desc")
    articles = cur.fetchall()
    if result > 0:
        return render_template("dashboard.html", articles=articles)
    else:
        msg = "No Articles Found!"
    return render_template('dashboard.html', msg=msg)
    # Close Connection 
    cur.close()

class ArticleForm(Form):
    title = StringField(u'主旨(Title)', validators=[validators.Length(min=1, max=200)])
    body = TextAreaField(u'本文(Body)', validators=[validators.Length(min=10)])

@app.route("/add_article", methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data 
        body = form.body.data
        # Create Cursor
        cur = mysql.connection.cursor()
        # Execute SQL
        cur.execute("INSERT into articles(title,body,author) values(%s,%s,%s)",(title,body,session['username']))
        # Commit to DB
        mysql.connection.commit()
        # Close Connection
        cur.close()
        flash('Article Created', 'success')
        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)    

# Edit Article
@app.route("/edit_article/<string:id>", methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # Create cursor 
    cur = mysql.connection.cursor()
    # Get article by id
    result = cur.execute("select * from articles where id = %s", [id])
    article = cur.fetchone()
    # Get Form
    form = ArticleForm(request.form)
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title'] 
        body = request.form['body'] 
        # Create Cursor
        cur = mysql.connection.cursor()
        # Execute SQL
        cur.execute("update articles set title=%s,body=%s where id=%s",(title,body,id))
        # Commit to DB
        mysql.connection.commit()
        # Close Connection
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for("dashboard"))
    return render_template("edit_article.html", form=form) 

# Delete Article
@app.route("/delete_article/<string:id>",methods=["POST"])
@is_logged_in
def delete_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()
    # Execute SQL
    cur.execute("Delete from articles where id = %s", [id])

    # Commit to DB
    mysql.connection.commit()
    # Close Connection
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for("dashboard"))


class MyForm(Form):
    first_name = StringField(u'First Name', validators=[validators.input_required()])
    last_name  = StringField(u'Last Name', validators=[validators.optional()])    


if __name__ == '__main__':
    app.run(debug=True)