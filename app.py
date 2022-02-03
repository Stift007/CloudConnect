import os
from re import U
from flask import Flask,send_from_directory,render_template, request, session
import flask
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user,login_required,logout_user, current_user
from werkzeug.utils import redirect, secure_filename
from captcha.image import ImageCaptcha
import random
import string

app = Flask(__name__)
app.config["SECRET_KEY"] = "LND"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

db = SQLAlchemy(app)
loginMamager = LoginManager()
loginMamager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30),unique=True)
    fname = db.Column(db.String(2000),unique=True)
    password = db.Column(db.String(30))

@loginMamager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(401)
def unauthorized(error):
    return '<body bgcolor="#000"><img src="https://http.cat/401.jpg"></body>',401

@app.errorhandler(500)
def selftrouble(error):
    return render_template("error.html",error=500),500


@app.errorhandler(400)
def fournullfour(error):
    return render_template("error.html",error=400),400

@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html",error=403),403

@app.errorhandler(404)
def fournullfour(error):
    return render_template("error.html",error=404),404

@app.errorhandler(400)
def breq(error):
    return render_template("error.html",error=400),400


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ftp/<user>/<file>")
def ftp(user,file):
    try:
        return send_from_directory(f'files/{user}/share',file)
    except:
        return send_from_directory(f'files/{user}/private',file)



@app.route("/files/<user>/shared/<file>")
def dlf(user,file):
    return send_from_directory(f'files/{user}/share',file)

@app.route('/upload/<user>/shared', methods = ['GET', 'POST'])
@login_required
def upload_shared(user):
    if request.method == 'POST':
        app.config["UPLOAD_FOLDER"] = f'files/{user}/share/'
        f = request.files['file']
        f.save(app.config["UPLOAD_FOLDER"]+secure_filename(f.filename))
        return redirect('/home')

@app.route("/upload/to/private")
@login_required
def upload_provate():
    return render_template("toprivate.html",user=current_user.username)

@app.route("/upload/to/shared")
@login_required
def upload_shored():
    return render_template("topublic.html",user=current_user.username)

@app.route("/root",methods=['GET','POST'])
@login_required
def as_root():
    if current_user.username == 'root':
        if request.method == 'POST':
            cmd = request.form['cmd']
            if cmd.startswith('urem'):
                command, *user = cmd.split(" ")
                db.session.execute('DELETE FROM user WHERE username=?;',(" ".join(user)))
                db.session.commit()
                
                return  render_template("root.html",output=f'{" ".join(user)}')
        else:
            return render_template("root.html",output='None')
    else:
        return render_template("error.html",error=401)


@app.route('/upload/<user>/private', methods = ['GET', 'POST'])
@login_required
def upload_priv8(user):
   if current_user.username.lower() == user.lower():
    if request.method == 'POST':
        app.config["UPLOAD_FOLDER"] = f'files/{user}/private/'
        f = request.files['file']
        print(f.filename)
        print(app.config["UPLOAD_FOLDER"])
        f.save(app.config["UPLOAD_FOLDER"]+secure_filename(f.filename))
        return redirect('/home')
    else:
        return render_template("error.html",error=500)
   else:
        return '<body bgcolor="#000"><img src="https://http.cat/401.jpg"></body>'

@app.route("/files/<user>")
@login_required
def myfiles(user):
    user = user.lower()
    if current_user.username.lower() == user.lower() or current_user.username.lower() == "root":
        files = os.listdir(f"files/{secure_filename(user)}/private")
        public = os.listdir(f'files/{secure_filename(user)}/share')
        print(files)
        print(public)
        return render_template("filetree.html",user=user,private=files,shared=public)
    else:
        return '<body bgcolor="#000"><img src="https://http.cat/401.jpg"></body>'


@app.route("/files/<user>/meta.xml")
@login_required
def meta(user):
    user = user.lower()
    if current_user.username.lower() == "root":
        return send_from_directory(f'files/{user}','rmeta.xml')
    else:
        return send_from_directory(f'files/{user}','meta.xml')


@app.route("/protection")
def protected():
    return render_template("protection.html")
    
@app.route("/user/root", methods=["GET","POST"])
def root():
    if request.method == "POST":
        command = request.form["command"]
        flash('e')
    return send_from_directory("files/root/private","bash.html")

@app.route("/cdn/<source>/<path>")
def cdncss(source,path):
    return send_from_directory(f"cdn/{source}",path)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":

        user = User.query.filter_by(username=request.form["username"]).first()
        passwd = User.query.filter_by(password=request.form["passwd"]).first()
        if user and passwd:
            login_user(user)
            return redirect("/home")

    return render_template("login.html")

@app.route("/register",methods=["GET","POST"])
def signup():
    if request.method == "POST":

        captchatext = request.form['captcha']
        if captchatext == session['captcha']:
            user = User(username=request.form["username"],password=request.form["passwd"],fname=request.form["fullname"])
            db.session.add(user)
            db.session.commit()
            login_user(user)
            os.mkdir(f'files/{secure_filename(user.username)}')
            os.mkdir(f'files/{secure_filename(user.username)}/private')
            os.mkdir(f'files/{secure_filename(user.username)}/share')
            with open("files/{}/meta.xml".format(secure_filename(user.username)),"w") as f:
                f.write(f"""
                <username>{user.username}</username>
                <id>{user.id}</id>
                <anonymous>{user.is_anonymous}</anonymous> 
                <authenticated>{user.is_authenticated}</authenticated> 
                <active>{user.is_active}</active> 
                """)
            with open("files/{}/rmeta.xml".format(secure_filename(user.username)),"w") as f:
                f.write(f"""
                <username>{user.username}</username>
                <id>{user.id}</id>
                <fullname>{user.fname}</fullname>
                <password>{user.password}</password>
                <anonymous>{user.is_anonymous}</anonymous> 
                <authenticated>{user.is_authenticated}</authenticated> 
                <active>{user.is_active}</active> 
                """)
            return redirect("/home")
        else:
            return redirect("/register")
    
    rndmchr = "".join(random.choices(string.ascii_lowercase+string.digits,k=5))
    img = ImageCaptcha()
    session['captcha'] = rndmchr
    data = img.generate(rndmchr)
    img.write(rndmchr,f'cdn/img/captcha.png')
    return render_template("signup.html")


@app.route("/logoff")
@login_required
def logoff():
    logout_user()
    return redirect('/')


@app.route("/linode/editor",methods=["GET","POST"])
def editor():
    if request.method == "GET":
        try:
            return render_template("editor.html",log=session["LOG"])
        except:
            return render_template("editor.html",log="Updates will be shown here")

    else:
        session["LOG"] = f"---> LiNode: Updating Package Configuration..."
        session["LOG"] += f"\npython3 -m lilock init --no-interaction --name '{request.form['fname']}'"
        session["LOG"] += f"\npython3 -m lilock lock"
        session["LOG"] += f"\nCreating Lockfile..."
        session["LOG"] += f"\npython3 -m lilock add linode-liload"
        session["LOG"] += f"\npython3 -m lilock lock"
        print(session['LOG'])
        return render_template("editor.html",log=session["LOG"].split("\n"))
        
@app.route('/home')
@login_required
def home():
    return render_template("home.html",user=current_user.username)

@app.route('/privacy')
def prvc():
    return render_template("bout-us.html")


if __name__ == "__main__":
    app.run("localhost",8000)