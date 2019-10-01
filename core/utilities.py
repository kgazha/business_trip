import requests
import json
import base64


def get_file_stream(data):
    url = 'http://datamart.gov74.ru/api/doctemplate/postdb'
    response = requests.post(url, json=data)
    response_data = json.loads(response.text)
    return base64.b64decode(response_data['Data'])


def send_email(address, sender_name, subject, body):
    url = "http://datamart.gov74.ru/api/doctemplate/SendMail"
    data = {
         "AddressTo": address,
         "SenderName": sender_name,
         "Subject": subject,
         "Body": body
    }
    requests.post(url, json=data)
