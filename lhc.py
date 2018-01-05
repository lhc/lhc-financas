# -*- coding: utf-8 -*-
import datetime

from flask import Flask, jsonify, request, render_template

import models

app = Flask(__name__)


def valid_entry(entry):
    # All fields are required
    return all([
        entry.get('entry_date'),
        entry.get('value'),
        entry.get('account'),
        entry.get('tags'),
        entry.get('description'),
    ])


@app.route('/new_entry', methods=['POST', ])
def new_entry():
    content = request.get_json()
    if valid_entry(content):
        new_entry = models.Entry(
            entry_date=content.get('entry_date'),
            value=content.get('value'),
            account=content.get('account'),
            tags=content.get('tags'),
            description=content.get('description'),
        )
        new_entry.save()
        return jsonify(**new_entry.to_dict()), 201
    else:
        return jsonify({'status': 'Bad Request'}), 400


@app.route('/report')
@app.route('/report/<year>')
def report(year=None):
    if year is None:
        year = datetime.date.today().year
    report_file = 'lhc_{year}.html'.format(year=year)
    return render_template(report_file)
