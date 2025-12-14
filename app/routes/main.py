from flask import Blueprint, render_template
from flask_login import current_user

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@bp.route('/about')
def about():
    """О системе"""
    return render_template('about.html')


@bp.route('/contact')
def contact():
    """Контакты"""
    return render_template('contact.html')


@bp.route('/help')
def help():
    """Справка"""
    return render_template('help.html')