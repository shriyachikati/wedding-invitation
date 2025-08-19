from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, NumberRange, InputRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

HERE = Path(__file__).resolve().parent
ROOT = HERE  # repo root where templates/ and static/ live

app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
db.init_app(app)

# --------- Database -------
class RSVP(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    engagement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prewedding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wedding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Asia/Kolkata')))

with app.app_context():
    db.create_all()




# ---------- Forms ----------
class RSVPForm(FlaskForm):
    first_name = StringField("FIRST NAME", validators=[DataRequired()])
    last_name  = StringField("LAST NAME",  validators=[DataRequired()])
    engagement_count = IntegerField(
        "Will you be attending our engagement? Please enter how many of you are attending the engagement",
        default=0,
        validators=[InputRequired(), NumberRange(min=0, max=10)]
    )
    prewedding_count = IntegerField(
        "Will you join us for the pre-wedding? Please enter how many of you will join us for the pre-wedding",
        default=0,
        validators=[InputRequired(), NumberRange(min=0, max=10)]
    )
    wedding_count  = IntegerField(
        "Will you be there at our wedding? Please enter how many of you will be there at out wedding",
        default=0,
        validators=[InputRequired(), NumberRange(min=0, max=10)]
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
            engagement_count=(form.engagement_count.data),
            prewedding_count=(form.prewedding_count.data),
            wedding_count=(form.wedding_count.data)
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
            func.sum(RSVP.engagement_count).label("engagement_count"),
            func.sum(RSVP.prewedding_count).label("prewedding_count"),
            func.sum(RSVP.wedding_count).label("wedding_count"),
        ).one()
    )

    return render_template("admin_rsvps.html", rows=rows, totals=totals)


if __name__ == "__main__":
    app.run(debug=False)
