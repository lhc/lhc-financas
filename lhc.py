# -*- coding: utf-8 -*-
import datetime

from flask import Flask, g, jsonify, request

import models

app = Flask(__name__)


@app.before_request
def before_request():
    g.db = models.db
    g.db.connect()


@app.after_request
def after_request(response):
    g.db.close()
    return response


def valid_payment(entry):
    # All fields are required
    return all([
        entry.get('entry_date'),
        entry.get('value'),
        entry.get('account'),
        entry.get('tags'),
        entry.get('description'),
    ])


@app.route('/notification/payment', methods=['POST', ])
def payment():
    content = request.get_json()
    if valid_payment(content):
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


@app.route('/notification/paypal/', methods=['POST', 'GET', ])
def paypal():
    txn_type = request.values.get('txn_type', None)
    item_name = request.values.get('item_name', '')
    first_name = request.values.get('first_name', '')
    last_name = request.values.get('last_name', '')

    if txn_type in ['subscr_payment', 'web_accept']:  # Payment received
        payment_date = request.values.get('payment_date', '')
        payment_date = datetime.datetime.strptime(payment_date, '%H:%M:%S %b %d, %Y PST')
        mc_gross = request.values.get('mc_gross', '')
        if txn_type == 'subscr_payment':
            payment_tags = ['mensalidade', ]
            tax_payment_tags = ['mensalidade', 'taxa']
        elif txn_type == 'web_accept':
            payment_tags = ['doacao', ]
            tax_payment_tags = ['doacao', 'taxa', ]

        payment_description = u'{0} - {1} {2}'.format(item_name, first_name, last_name)
        tax_payment_description = u'{0} - Taxa {1} {2}'.format(item_name, first_name, last_name)

        new_entry = models.Entry(
            entry_date=payment_date.strftime('%Y-%m-%d'),
            value='%.2f' % float(mc_gross),
            account='_paypal',
            tags=','.join(payment_tags),
            description=payment_description,
        )
        new_entry.save()

        new_entry = models.Entry(
            entry_date=payment_date.strftime('%Y-%m-%d'),
            value='%.2f' % float(mc_gross),
            account='_paypal',
            tags=','.join(tax_payment_tags),
            description=tax_payment_description,
        )
        new_entry.save()

    return "OK"


@app.route('/report', methods=['GET', ])
def report():
    entries = models.Entry.select()
    with open('money_template.html', 'r') as template:
        moneylog_entries = '\n'.join([entry.money_log for entry in entries])
        template_content = template.read()
        report_content = template_content.replace(
            '[CONTEUDO]', moneylog_entries.encode('utf-8'))
    return report_content


if __name__ == "__main__":
    app.debug = True
    app.run()


# @app.route("/notification/paypal/", methods=["POST", "GET", ])
# def paypal():
#     received_data = str(request.values)

#     txn_type = request.values.get('txn_type', None)
#     item_name = request.values.get('item_name', '')
#     first_name = request.values.get('first_name', '')
#     last_name = request.values.get('last_name', '')

#     if txn_type in ['subscr_payment', 'web_accept']:  # Payment received
#         payment_date = request.values.get('payment_date', '')
#         payment_date = datetime.datetime.strptime(payment_date, '%H:%M:%S %b %d, %Y PST')
#         mc_gross = request.values.get('mc_gross', '')
#         if txn_type == 'subscr_payment':
#             payment_tags = ['_paypal', 'mensalidade']
#             tax_payment_tags = ['_paypal', 'mensalidade', 'taxa']
#         elif txn_type == 'web_accept':
#             payment_tags = ['_paypal', 'doacao']
#             tax_payment_tags = ['_paypal', 'doacao', 'taxa']

#         mc_fee = float(request.values.get('mc_fee', '0'))

#         payment_description = u'{0} - {1} {2}'.format(item_name, first_name, last_name)
#         tax_payment_description = u'{0} - Taxa {1} {2}'.format(item_name, first_name, last_name)

#         new_lines.append(PAYMENT_TEMPLATE.format(**{
#             'payment_date': payment_date.strftime('%Y-%m-%d'),
#             'payment_value': '%.2f' % float(mc_gross),
#             'payment_tags': ','.join(payment_tags),
#             'payment_description': payment_description.encode('utf-8')
#         }))

#         new_lines.append(PAYMENT_TEMPLATE.format(**{
#             'payment_date': payment_date.strftime('%Y-%m-%d'),
#             'payment_value': '%.2f' % -mc_fee,
#             'payment_tags': ','.join(tax_payment_tags),
#             'payment_description': tax_payment_description.encode('utf-8')
#         }))

#     elif txn_type == 'subscr_signup':  # New subscription
#         subscr_date = request.values.get('subscr_date', '')
#         subscr_date = datetime.datetime.strptime(subscr_date, '%H:%M:%S %b %d, %Y PST')

#         mc_amount3 = request.values.get('mc_amount3', '')
#         payment_tags = [u'_paypal', 'mensalidade', u'previsao']
#         payment_description = u'Previsao {0} - {1} {2}'.format(item_name, first_name, last_name)

#         new_lines.append(PAYMENT_TEMPLATE.format(**{
#             'payment_date': subscr_date.strftime('%Y-%m-%d'),
#             'payment_value': '%.2f' % float(mc_amount3),
#             'payment_tags': ','.join(payment_tags),
#             'payment_description': payment_description.encode('utf-8')
#         }))

#     with open('lhc2016real.txt', 'a') as money_file:
#         for line in new_lines:
#             money_file.write(line)
#             money_file.write('\n')

#     update_html_report()

#     return "OK"
