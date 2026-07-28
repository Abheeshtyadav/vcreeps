import os
import requests
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key_change_in_prod")

IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "28208ececb3d9428110c0e8f3c72d018")
DATABASE_URL = os.environ.get("DATABASE_URL")


if DATABASE_URL:
  
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
   
    if os.path.exists("/tmp"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/local_test.db"
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'local_test.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    aname = db.Column("aname", db.String(100), nullable=True)
    desc = db.Column("desc", db.Text, nullable=False)
    contact = db.Column("contact", db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)

class remove(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    vname = db.Column("vname", db.String(100), nullable=True)
    idd = db.Column("idd", db.Integer, nullable=False)
    desc = db.Column("desc", db.Text, nullable=False)

with app.app_context():
    db.create_all()

def get_http_session():
    """Configures a resilient HTTP session for API requests."""
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return session

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/test")
def test():
    data = users(aname="Test Name", desc="Test Description", contact="Test Contact")
    db.session.add(data)
    db.session.commit()
    return "Database test record added successfully!"

@app.route("/creep", methods=["POST", "GET"])
def picu():
    if request.method == "POST":
        uname = request.form.get("aname")
        ureview = request.form.get("desc")
        contact = request.form.get("contact")
        
        files = request.files.getlist("review_images")
        image_urls = []
        
        http_session = get_http_session()

        for file in files:
            if file and file.filename != "":
                filestream = file.read()
                payload = {"key": IMGBB_API_KEY}
                files_payload = {"image": (file.filename, filestream)}
                
                try:
                    response = http_session.post(
                        "https://api.imgbb.com/1/upload", 
                        data=payload, 
                        files=files_payload,
                        timeout=(10, 30)
                    )
                    json_data = response.json()
                    
                    if json_data.get("success"):
                        image_urls.append(json_data["data"]["url"])
                    else:
                        print(f"ImgBB returned API error: {json_data}")
                except Exception as e:
                    print(f"Error transferring file to ImgBB: {e}")
        
        images_string = ",".join(image_urls) if image_urls else None
        
        data = users(aname=uname, contact=contact, desc=ureview, images=images_string)
        db.session.add(data)
        db.session.commit()
        
        flash("Successfully submitted the report.", "success")
        return redirect(url_for("show"))

    return render_template("report.html")

@app.route("/show")
def show():
    raw_data = users.query.all()
    
    for item in raw_data:
        if item.images:
            item.image_list = [url.strip() for url in item.images.split(",") if url.strip()]
        else:
            item.image_list = []
            
    return render_template("show.html", data=raw_data)

if __name__ == "__main__":
    app.run(debug=False)