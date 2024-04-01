from flask import Blueprint, render_template

statistics = Blueprint(
    "statistics",
    __name__,
    template_folder="templates/statistics",
    url_prefix="/statistics",
)

@statistics.route("/")
def statistics_index():
    return render_template("statistics/main.j2")
