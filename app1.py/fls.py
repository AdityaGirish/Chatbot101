from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

@app.route('/')
def hello_world():
    return render_template('hello.html')

if __name__ == '__main__':
    app.run()
