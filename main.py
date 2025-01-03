from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from datetime import datetime
import re
from setting import settings
import os

app = Flask(__name__)
print(settings.db_url)
app.config["MONGO_URI"] = settings.db_url
mongo = PyMongo(app)

# MongoDB Collection
deployments = mongo.db.deployments


@app.route("/", methods=["GET"])
def list_deployments():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    query = {}
    if search:
        regex = re.compile(f".*{re.escape(search)}.*", re.IGNORECASE)
        query["$or"] = [
            {"service_changed": regex},
            {"pr_link": regex},
            {"jira_notion_link": regex},
            {"pr_raised_by": regex},
            {"pr_reviewed_by": regex},
            {"pr_merged_by": regex},
            {"description": regex},
            {"breaking_changes": regex},
            {"test_cases": regex},
        ]

    if start_date and end_date:
        query["deployment_date"] = {
            "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
            "$lte": datetime.strptime(end_date, "%Y-%m-%d"),
        }

    total = deployments.count_documents(query)
    deployment_list = (
        deployments.find(query)
        .sort("deployment_date", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    return render_template(
        "index.html",
        deployments=list(deployment_list),
        page=page,
        per_page=per_page,
        total=total,
    )


@app.route("/add", methods=["POST"])
def add_deployment():
    data = request.json
    deployment = {
        "deployment_date": datetime.strptime(data["deployment_date"], "%Y-%m-%d"),
        "service_changed": data.get("service_changed", ""),
        "pr_link": data.get("pr_link", ""),
        "jira_notion_link": data.get("jira_notion_link", ""),
        "pr_raised_by": data.get("pr_raised_by", ""),
        "pr_reviewed_by": data.get("pr_reviewed_by", ""),
        "pr_merged_by": data.get("pr_merged_by", ""),
        "description": data.get("description", ""),
        "breaking_changes": data.get("breaking_changes", ""),
        "test_cases": data.get("test_cases", ""),
    }
    deployment_id = deployments.insert_one(deployment).inserted_id
    return (
        jsonify({"message": "Deployment added successfully", "id": str(deployment_id)}),
        201,
    )


if __name__ == "__main__":
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", False) == "True"
    app.run(debug=debug, host=host, port=port)
