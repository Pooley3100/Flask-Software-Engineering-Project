from flask import Blueprint, redirect, url_for, render_template
from Flask_Cinema_Site import app

home_blueprint = Blueprint(
    'home', __name__,
    template_folder='templates',
    static_folder='static'
)

@app.route('/', methods=['GET'])
def boot():
    return redirect(url_for('home.home'))

@home_blueprint.route('/', methods=['GET'])
def home():
    return render_template('home_base.html')
    #return redirect(url_for('movie.view_multiple'))
