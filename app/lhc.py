# -*- coding: utf-8 -*-
import datetime
import requests

from flask import Flask, jsonify, request, render_template

import models

PAYPAL_PRODUCTION = 'https://ipnpb.paypal.com/cgi-bin/webscr'

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


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


@app.route('/paypal/notification', methods=['POST', ])
def paypal_notification():
    ''' Listener for PayPal notification '''
    notification = request.form.to_dict()

    notification['cmd'] = '_notify-validate'
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'host': 'www.paypal.com'
    }
    validation_response = requests.post(
        PAYPAL_PRODUCTION,
        data=notification,
        headers=headers,
        verify=True)
    validation_response.raise_for_status()

    if validation_response == 'VERIFIED':
        full_name = ' '.join([
            notification.get('first_name', ''),
            notification.get('last_name', ''),
        ])
        value = notification.get('mc_gross', '0')
        tax_value = '-{}'.format(notification.get('mc_fee', '0'))
        entry_date = ''

        account = '_paypal'
        description = '{} - {}'.format(
            notification.get('item_name'),
            full_name)
        tax_description = 'Taxa - {}'.format(description)

        tags = 'mensalidade' if 'mensalidade' in description.lower() else ''

        entry = models.Entry(
            entry_date=entry_date,
            value=value,
            account=account,
            tags=tags,
            description=description
        )
        entry.save()

        tax_entry = models.Entry(
            entry_date=entry_date,
            value=tax_value,
            account=account,
            tags='taxa,{}'.format(tags),
            description=tax_description
        )
        tax_entry.save()

    return ''
