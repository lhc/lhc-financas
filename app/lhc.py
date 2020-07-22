# -*- coding: utf-8 -*-
import datetime
import re

import requests

from flask import Flask, jsonify, request, render_template

import models

PAYPAL_PRODUCTION = "https://ipnpb.paypal.com/cgi-bin/webscr"

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def valid_entry(entry):
    # All fields are required
    return all(
        [
            entry.get("entry_date"),
            entry.get("value"),
            entry.get("account"),
            entry.get("tags"),
            entry.get("description"),
        ]
    )


@app.route("/new_entry", methods=["POST"])
def new_entry():
    content = request.get_json()
    if valid_entry(content):
        new_entry = models.Entry(
            entry_date=content.get("entry_date"),
            value=content.get("value"),
            account=content.get("account"),
            tags=content.get("tags"),
            description=content.get("description"),
        )
        new_entry.save()
        return jsonify(**new_entry.to_dict()), 201
    else:
        return jsonify({"status": "Bad Request"}), 400


@app.route("/report")
@app.route("/report/<year>")
def report(year=None):
    if year is None:
        year = datetime.date.today().year
    report_file = "lhc_{year}.html".format(year=year)
    return render_template(report_file)


@app.route("/status")
def status():
    month = datetime.date.today().month
    year = datetime.date.today().year

    past_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    past_year = year - 1 if past_month == 12 else year
    next_year = year + 1 if next_month == 1 else year

    regular_expenses_tags = ["aluguel", "cpfl", "net", "sanasa", "vivo"]

    regular_expenses_actual_month = models.Entry.select().where(
        (models.Entry.entry_date >= datetime.date(year, month, 1))
        & (models.Entry.entry_date < datetime.date(next_year, next_month, 1))
        & (models.Entry.tags.in_(regular_expenses_tags))
    )
    regular_expenses_actual = abs(
        sum([entry.value for entry in regular_expenses_actual_month])
    )
    regular_expenses_past_month = models.Entry.select().where(
        (models.Entry.entry_date < datetime.date(year, month, 1))
        & (models.Entry.entry_date >= datetime.date(past_year, past_month, 1))
        & (models.Entry.tags.in_(regular_expenses_tags))
    )
    regular_expenses_past = abs(
        sum([entry.value for entry in regular_expenses_past_month])
    )

    tags_already_spent = []
    regular_expenses_estimate = 0
    for entry in regular_expenses_actual_month:
        regular_expenses_estimate += abs(entry.value)
        tags_already_spent.append(entry.tags)
    for entry in regular_expenses_past_month:
        if entry.tags not in tags_already_spent:
            regular_expenses_estimate += abs(entry.value)

    actual_incomes = models.Entry.select().where(
        (models.Entry.entry_date < datetime.date(next_year, next_month, 1))
        & (models.Entry.entry_date >= datetime.date(year, month, 1))
        & (models.Entry.value > 0)
        & (~models.Entry.tags.in_(["transferencia", "inicial", "aporteinicial"]))
    )
    total_incomes = abs(sum([entry.value for entry in actual_incomes]))

    actual_expenses = models.Entry.select().where(
        (models.Entry.entry_date < datetime.date(next_year, next_month, 1))
        & (models.Entry.entry_date >= datetime.date(year, month, 1))
        & (models.Entry.value < 0)
        & (~models.Entry.tags.in_(regular_expenses_tags))
        & (~models.Entry.tags.in_(["transferencia", "inicial", "aporteinicial"]))
    )
    total_expenses = abs(sum([entry.value for entry in actual_expenses]))

    return (
        jsonify(
            {
                "actual_incomes": str(total_incomes),
                "actual_expenses": str(total_expenses),
                "regular_expenses_estimate": str(regular_expenses_estimate),
                "regular_expenses_actual": str(regular_expenses_actual),
                "regular_expenses_past": str(regular_expenses_past),
            }
        ),
        200,
    )


@app.route("/paypal/notification", methods=["POST"])
def paypal_notification():
    """ Listener for PayPal notification """
    notification = request.form.to_dict()

    notification["cmd"] = "_notify-validate"
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "host": "www.paypal.com",
    }
    validation_response = requests.post(
        PAYPAL_PRODUCTION, data=notification, headers=headers, verify=True
    )
    validation_response.raise_for_status()

    valid_txn_types = ("subscr_payment", "web_accept")
    txn_type = notification.get("txn_type")
    if validation_response.text == "VERIFIED" and txn_type in valid_txn_types:
        full_name = " ".join(
            [notification.get("first_name", ""), notification.get("last_name", "")]
        )
        value = notification.get("mc_gross", "0")
        tax_value = "-{}".format(notification.get("mc_fee", "0"))

        payment_date = notification.get("payment_date", "")
        match = re.findall("[A-Za-z]{3} [0-9]{2}, [0-9]{4}", payment_date)
        if match:
            raw_payment_date = match.pop()
            entry_date = datetime.datetime.strptime(raw_payment_date, "%b %d, %Y")
            entry_date = entry_date.strftime("%Y-%m-%d")

        if "cnpj" in notification.get("item_number", ""):
            account = "_paypal_lhc"
        else:
            account = "_paypal"

        description = "{} - {}".format(notification.get("item_name"), full_name)
        tax_description = "Taxa - {}".format(description)

        tags_map = {
            "camiseta-30": "camisetas",
            "lhc-85": "mensalidade",
            "lhc-110": "mensalidade",
            "lhc-60": "mensalidade",
            "lhc-70": "mensalidade",
            "lhc-30": "contribuicao",
            "doacao-lhc": "doacao",
            "aporteinicial": "aporteinicial",
            "lhc-cnpj-85": "mensalidade",
            "lhc-cnpj-110": "mensalidade",
            "lhc-cnpj-70": "mensalidade",
            "lhc-cnpj-30": "contribuicao",
            "contribuicao-lhc-30": "contribuicao",
            "starving-hacker": "mensalidade",
        }
        tags = tags_map.get(notification.get("item_number", ""), "")

        entry = models.Entry(
            entry_date=entry_date,
            value=value,
            account=account,
            tags=tags,
            description=description,
        )
        entry.save()

        tax_entry = models.Entry(
            entry_date=entry_date,
            value=tax_value,
            account=account,
            tags="taxa,{}".format(tags),
            description=tax_description,
        )
        tax_entry.save()

    return ""


if __name__ == "__main__":
    app.run()
