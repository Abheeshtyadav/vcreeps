from flask import Flask,render_template,redirect,url_for,flash,request
import requests
import os
from flask_sqlalchemy import SQLAlchemy


IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')

app=Flask(__name__)
app.secret_key="gfsdhjg"
database_url = os.environ.get("DATABASE_URL")
if os.environ.get("FLASK_ENV") == "development" or not database_url:
   
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'local_test.db')}"
else:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    aname=db.Column("aname",db.String(100),nullable=True)
    desc=db.Column("desc",db.Text,nullable=False)
    contact=db.Column("contact",db.Text,nullable=False)
    images = db.Column(db.Text, nullable=True)


class remove(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    vname=db.Column("vname",db.String(100),nullable=True)
    idd=db.Column("idd",db.Integer,nullable=False)
    desc=db.Column("desc",db.Text,nullable=False)






@app.route("/")
def home():
    return render_template("home.html")

@app.route("/test")
def test():
    data=users(aname="dsgjhfgsd",desc="sdgfg",contact="dgsfd")
    db.session.add(data)
    db.session.commit()
    return "done"


@app.route("/creep", methods=["POST", "GET"])
def picu():

    if request.method == "POST":
        uname = request.form.get("aname")
        ureview = request.form.get("desc")
        contact=request.form.get("contact")
        
        """ roomt = request.form.get("room_type")
        if not roomt:
            roomt = "Not Specified" """
            
        
        files = request.files.getlist('review_images')
        image_urls = []

        for file in files:
            if file and file.filename != '':
                filestream = file.read()
                payload = {'key':"28208ececb3d9428110c0e8f3c72d018"}
                files_payload = {'image': (file.filename, filestream)}
                
                try:
                    response = requests.post('https://api.imgbb.com/1/upload', data=payload, files=files_payload)
                    json_data = response.json()
                    
                    if json_data.get('success'):
                        image_urls.append(json_data['data']['url'])
                except Exception as e:
                    print(f"Error transferring file to ImgBB: {e}")
                   
        
        
        images_string = ",".join(image_urls) if image_urls else None
        
        
        data = users(aname=uname,contact=contact, desc=ureview, images=images_string)
        
        db.session.add(data)
        db.session.commit()
        
        flash("Successfully added your pic", "success")
        return redirect(url_for("home"))

    return render_template("report.html")

@app.route("/show")
def show():
    raw_data = users.query.all()
    
    # Convert comma-separated string into an array of URLs for every record
    for item in raw_data:
        if item.images:
            item.image_list = [url.strip() for url in item.images.split(",") if url.strip()]
        else:
            item.image_list = []
            
    return render_template("show.html", data=raw_data)


@app.before_request
def initialize_database():
    db.create_all()


if "__main__" ==  __name__:
    app.run(debug=True)