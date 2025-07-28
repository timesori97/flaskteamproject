from flask import Blueprint, request, render_template, redirect
from models import db, Member

bp = Blueprint('signup', __name__, url_prefix='/signup')

@bp.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        existing_user = Member.query.filter_by(email=email).first()
        if existing_user :
            return "이미 가입된 계정입니다.", 400
        
        # 회원가입 처리
        user = Member(email=email, password=password, name=name)
        db.session.add(user)
        db.session.commit()
        
        return redirect('/')
    
    return render_template('signup.html')
        