from flask import Blueprint, redirect, session

bp = Blueprint('logout', __name__, url_prefix='/logout')

@bp.route('/', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')
