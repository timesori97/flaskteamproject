from flask import Flask, render_template, request, session, redirect, url_for, flash
from models import db, Member, Translation
from signup import bp as signup_bp
from login import bp as login_bp
from logout import bp as logout_bp
from google.cloud import translate_v2
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1111@localhost:3306/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Blueprint 등록
app.register_blueprint(signup_bp)
app.register_blueprint(login_bp)
app.register_blueprint(logout_bp)

# DB 연결
db.init_app(app)

# 지원 언어 목록
LANGUAGES = {
    'ko': '한국어',
    'en': '영어',
    'ja': '일본어',
    'zh-CN': '중국어',
    'ru': '러시아어'
}

def translate_text(text, target_lang, source_lang=None):
    try:
        translate_client = translate_v2.Client()
        detected_lang = source_lang
        if not source_lang:
            detection = translate_client.detect_language(text)
            detected_lang = detection['language']
        if detected_lang == target_lang:
            raise ValueError("소스 언어와 대상 언어는 달라야 합니다.")
        result = translate_client.translate(text, target_language=target_lang, source_language=source_lang or detected_lang)
        return {
            'source_language': detected_lang,
            'original_text': result['input'],
            'translated_text': result['translatedText']
        }
    except Exception as e:
        print(f"번역 오류: {str(e)}")
        flash(f"번역 중 오류 발생: {str(e)}", 'error')
        return {'error': f"번역 중 오류 발생: {str(e)}"}

@app.route('/')
def home():
    return redirect(url_for('translate'))

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    result_data = None
    input_text = ''
    source_lang = 'auto'
    target_lang = 'zh-CN'  # 기본값을 zh-CN으로 변경 (UI 기본값 동기화)

    if request.method == 'POST':
        action = request.form.get('action')
        input_text = request.form.get('text', '')
        source_lang = request.form.get('source_lang', 'auto')
        target_lang = request.form.get('target_lang')  # 기본값 제거

        print(f"입력: text={input_text}, source_lang={source_lang}, target_lang={target_lang}, action={action}")

        if action == 'swap':
            input_text = request.form.get('last_output', '')
            source_lang, target_lang = target_lang, source_lang

        if not target_lang:
            flash('대상 언어를 선택하세요.', 'error')
        elif source_lang != 'auto' and source_lang == target_lang:
            flash('소스 언어와 대상 언어는 달라야 합니다.', 'error')
        elif not input_text:
            flash('번역할 내용을 입력하세요.', 'error')
        else:
            result_data = translate_text(input_text, target_lang, source_lang if source_lang != 'auto' else None)
            print(f"번역 결과: {result_data}")
            if 'error' not in result_data:
                if 'user_email' in session:
                    user = Member.query.filter_by(email=session['user_email']).first()
                    if user:
                        translation = Translation(
                            member_id=user.id,
                            source_lang=result_data['source_language'],
                            target_lang=target_lang,
                            original_text=result_data['original_text'],
                            after=result_data['translated_text']
                        )
                        db.session.add(translation)
                        db.session.commit()
                        result_data['translation_id'] = translation.id
                    else:
                        flash('사용자 정보를 찾을 수 없습니다. 다시 로그인하세요.', 'error')
                flash('번역이 완료되었습니다!', 'success')

    return render_template('translate.html', languages=LANGUAGES, input_text=input_text,
                         source_lang=source_lang, target_lang=target_lang, translated_text=result_data)

@app.route('/mypage')
def mypage():
    if 'user_email' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login.login'))
    user = Member.query.filter_by(email=session['user_email']).first()
    if not user:
        flash('사용자 정보를 찾을 수 없습니다. 다시 로그인하세요.', 'error')
        return redirect(url_for('login.login'))
    translations = Translation.query.filter_by(member_id=user.id).order_by(Translation.created_at.desc()).all()
    return render_template('mypage.html', translations=translations, languages=LANGUAGES)

@app.route('/translation/<int:id>')
def view_translation(id):
    translation = Translation.query.get_or_404(id)
    if 'user_email' not in session or Member.query.filter_by(email=session['user_email']).first().id != translation.member_id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('translate'))
    return render_template('view_translation.html', source_lang=translation.source_lang,
                         target_lang=translation.target_lang, before_text=translation.original_text,
                         after_text=translation.after, languages=LANGUAGES, id=id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')