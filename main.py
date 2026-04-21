from flask import Flask, render_template
app = Flask(__name__)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')
    @app.route('/')
def index():
    return render_template('index.html')
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/register')
def signup():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)