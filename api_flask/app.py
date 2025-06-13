from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, date
import os

# Serve files out of api_flask/static
app = Flask(__name__, static_folder="static")
CORS(app)

# Root URL → serve the front-end index.html
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")

# Your existing screening endpoint
@app.route("/assess", methods=["POST"])
def assess():
    data     = request.get_json()
    age      = data.get("age", 0)
    subgroup = data.get("subgroup", "")
    last     = data.get("last_screenings", {})
    risk     = data.get("risk_factors", {})
    today    = date.today()
    recs     = []

    # Baseline multipliers
    subgroup_baseline = {
        "Asian Indian": 0.88,
    "Chinese": 1.31,
    "Filipino": 1.13,
    "Japanese": 0.95,
    "Korean": 1.27,
    "Vietnamese": 1.26,
    "Other Asian": 1.03,
    }

    def compute_personal_multiplier(risk):
        m = 1.0
        if risk.get("family_history"):
            m *= 1.5
        bmi = risk.get("BMI")
        if isinstance(bmi, (int, float)) and bmi >= 30:
            m *= 1.2
        return m

    guidelines = {
        "breast":     {"min": 40, "max": 74, "interval": 2},
        "cervical":   {"min": 21, "max": 65, "interval": 3},
        "colorectal": {"min": 50, "max": 75, "interval": 1},
    }

    if subgroup in subgroup_baseline:
        for kind, cfg in guidelines.items():
            if cfg["min"] <= age <= cfg["max"]:
                ld_iso = last.get(kind)
                if ld_iso:
                    d0 = datetime.fromisoformat(ld_iso).date()
                else:
                    d0 = date(1970,1,1)
                due_date = d0.replace(year=d0.year + cfg["interval"])
                if today >= due_date:
                    base     = subgroup_baseline[subgroup]
                    personal = compute_personal_multiplier(risk)
                    score    = round(base * personal, 2)
                    if score >= 1.6: tier = "High"
                    elif score >= 1.2: tier = "Moderate"
                    else: tier = "Routine"
                    recs.append({
                        "screening":  kind,
                        "priority":   tier,
                        "risk_score": score
                    })
    return jsonify(recommendations=recs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
