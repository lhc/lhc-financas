#-*- coding: utf-8 -*-
from flask import Flask, jsonify, request

import models

app = Flask(__name__)


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
        return jsonify({'status':'Bad Request'}), 400


if __name__ == "__main__":
    app.debug = True
    app.run()







# import datetime
# import logging

# from flask import Flask, request


# logger = logging.getLogger("payments")
# logger.setLevel(logging.INFO)

# # create a file handler
# handler = logging.FileHandler('payments.log')
# handler.setLevel(logging.INFO)

# # create a logging format
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)

# # add the handlers to the logger
# logger.addHandler(handler)

# app = Flask("app")
# app.debug = True

# PAYMENT_TEMPLATE = '{payment_date}\t{payment_value}\t\t{payment_tags}|{payment_description}'


# @app.route("/notification/paypal/", methods=["POST", "GET", ])
# def paypal():
#     received_data = str(request.values)
#     logger.info(received_data)

#     txn_type = request.values.get('txn_type', None)
#     item_name = request.values.get('item_name', '')
#     first_name = request.values.get('first_name', '')
#     last_name = request.values.get('last_name', '')

#     logger.info(txn_type)

#     new_lines = []
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


# @app.route("/notification/payment/", methods=["POST", "GET", ])
# def payment():
#     received_data = str(request.values)
#     logger.info(received_data)

#     new_lines = []
#     new_lines.append(PAYMENT_TEMPLATE.format(**{
#         'payment_date': request.values.get('payment_date').encode('utf-8'),
#         'payment_value': '%.2f' % float(request.values.get('payment_value').encode('utf-8')),
#         'payment_tags': request.values.get('payment_tags').encode('utf-8'),
#         'payment_description': request.values.get('payment_description').encode('utf-8')
#     }))

#     with open('lhc2016real.txt', 'a') as money_file:
#         for line in new_lines:
#             money_file.write(line)
#             money_file.write('\n')

#     update_html_report()

#     return "OK"


# def update_html_report():
#     with open('lhc2016real.txt', 'r') as money_file:
#         money_data = money_file.read()

#     with open('money_template.html', 'r') as money_template:
#         template = money_template.read()
#         template = template.replace('[CONTEUDO]', money_data)

#     with open('/var/www/apps/blog/lhc.html', 'w') as final_report:
#         final_report.write(template)

