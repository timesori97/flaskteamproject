from flask import Blueprint, request, render_template, session, redirect
from models import Member

bp = Blueprint('login', __name__, url_prefix='/login')

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Member.query.filter_by(email=email).first()

        if not user:
            return "존재하지 않는 이메일입니다.", 400

        if user.password != password:
            return "비밀번호가 틀렸습니다.", 400

        # 로그인 성공 → 세션 저장
        session['user_email'] = user.email
        session['user_password'] = user.password

        return redirect('/')

    return render_template('base.html')


