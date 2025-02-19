from datetime import datetime as dt

from flask import render_template, request
from flask_login import current_user, login_required

from approve.main.routes import bp
from approve.main.utils import role_forbidden
from approve.models import EventType, Order, OrderEvent, UserRoles
from approve.utils import get_filter_timestamps

################################################################################
# Responibility page
################################################################################


@bp.route("/history/", methods=["GET", "POST"])
@login_required
@role_forbidden([UserRoles.default, UserRoles.vendor])
def ShowHistory():
    dates = get_filter_timestamps()
    filter_from = request.args.get("from", default=dates["recently"], type=int)
    dates["сегодня"] = dates.pop("daily")
    dates["неделя"] = dates.pop("weekly")
    dates["месяц"] = dates.pop("monthly")
    dates["квартал"] = dates.pop("quarterly")
    dates["год"] = dates.pop("annually")
    dates["недавно"] = dates.pop("recently")
    events = OrderEvent.query.filter(OrderEvent.timestamp > dt.fromtimestamp(filter_from))
    events = events.join(Order).filter_by(hub_id=current_user.hub_id)
    events = events.order_by(OrderEvent.timestamp.desc()).all()
    return render_template(
        "main/history/history.html", events=events, EventType=EventType, filter_from=filter_from, dates=dates
    )
