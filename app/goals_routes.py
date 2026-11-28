from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Member, ReadingGoal
from app.goals import finished_books, books_finished_in_month, current_streak

goals_bp = Blueprint("goals_bp", __name__, url_prefix="/goals")


@goals_bp.route("/", methods=["GET", "POST"])
@login_required
def goals_page():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Sirf members goal set kar sakte hain.")
        return redirect(url_for("auth.dashboard"))

    today = date.today()
    goal = ReadingGoal.query.filter_by(
        member_id=member.id, year=today.year, month=today.month
    ).first()

    if request.method == "POST":
        action = request.form.get("action", "save")

        if action == "delete":
            if goal:
                db.session.delete(goal)
                db.session.commit()
                flash("Is mahine ka goal hata diya gaya.")
            return redirect(url_for("goals_bp.goals_page"))

        target = request.form.get("target", type=int)
        if target is None or target < 1 or target > 100:
            flash("Target 1 se 100 ke beech daalein.")
            return redirect(url_for("goals_bp.goals_page"))

        if goal:
            goal.target = target
        else:
            db.session.add(ReadingGoal(
                member_id=member.id, year=today.year, month=today.month, target=target
            ))
        db.session.commit()
        flash("Goal save ho gaya.")
        return redirect(url_for("goals_bp.goals_page"))

    done_list = finished_books(member.id, today.year, today.month)
    done = len(done_list)

    percent, remaining, achieved = 0, 0, False
    if goal:
        percent = min(100, int(done * 100 / goal.target))
        remaining = max(0, goal.target - done)
        achieved = done >= goal.target

    all_goals = ReadingGoal.query.filter_by(member_id=member.id).all()
    goal_map = {(g.year, g.month): g.target for g in all_goals}
    streak = current_streak(member.id, goal_map)

    history = []
    for g in sorted(all_goals, key=lambda x: (x.year, x.month), reverse=True):
        if (g.year, g.month) == (today.year, today.month):
            continue
        finished = books_finished_in_month(member.id, g.year, g.month)
        history.append({
            "label": date(g.year, g.month, 1).strftime("%B %Y"),
            "target": g.target,
            "done": finished,
            "ok": finished >= g.target,
        })

    return render_template(
        "goals.html",
        goal=goal,
        done=done,
        done_list=done_list,
        percent=percent,
        remaining=remaining,
        achieved=achieved,
        streak=streak,
        history=history,
        month_name=today.strftime("%B %Y"),
    )