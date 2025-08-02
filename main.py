from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, case
from datetime import datetime
import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
db.init_app(app)

# --------- Database -------
class RSVP(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    attending_engagement: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attending_pre_wedding: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attending_wedding: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Asia/Kolkata')))

with app.app_context():
    db.create_all()

# ---------- Forms ----------
class RSVPForm(FlaskForm):
    first_name = StringField("FIRST NAME", validators=[DataRequired()])
    last_name  = StringField("LAST NAME",  validators=[DataRequired()])
    attending_engagement = RadioField(
        "Will you be attending our engagement?",
        choices=[("yes", "Yes!"), ("no", "No, sorry.")],
        validators=[DataRequired()]
    )
    attending_pre_wedding = RadioField(
        "Will you join us for the pre-wedding?",
        choices=[("yes", "Yes!"), ("no", "No, sorry.")],
        validators=[DataRequired()]
    )
    attending_wedding  = RadioField(
        "Will you be there at our wedding?",
        choices=[("yes", "Yes!"), ("no", "No, sorry.")],
        validators=[DataRequired()]
    )
    submit = SubmitField("Submit RSVP")

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/the-venue")
def venue():
    return render_template("venue.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")


@app.route("/rsvp", methods=["GET", "POST"])
def rsvp():
    form = RSVPForm()
    if form.validate_on_submit():
        rsvp = RSVP(
            first_name=form.first_name.data.strip().title(),
            last_name=form.last_name.data.strip().title(),
            attending_engagement=(form.attending_engagement.data == "yes"),
            attending_pre_wedding=(form.attending_pre_wedding.data == "yes"),
            attending_wedding=(form.attending_wedding.data == "yes")
        )
        db.session.add(rsvp)
        db.session.commit()
        return render_template("rsvp_thankyou.html", rsvp=rsvp)
    return render_template("rsvp.html", form=form)


@app.route("/rsvp-list", methods=["GET"])
def admin_rsvps():
    """Show every RSVP in a plain table (GET only)."""
    rows = RSVP.query.order_by(RSVP.submitted_at.desc()).all()
    totals = (
        db.session.query(
            func.count(case((RSVP.attending_engagement, 1))).label("attending_engagement"),
            func.count(case((RSVP.attending_pre_wedding, 1))).label("attending_pre_wedding"),
            func.count(case((RSVP.attending_wedding, 1))).label("attending_wedding"),
        )
        .one()
    )
    return render_template("admin_rsvps.html", rows=rows, totals=totals)


if __name__ == "__main__":
    app.run(debug=True)
