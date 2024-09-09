from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "some_super_secret_key"


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("form.html")


if __name__ == "__main__":
    app.run(debug=True)
