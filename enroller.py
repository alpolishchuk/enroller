# -*- coding: utf-8 -*-
import sys
import os
import zipfile
import time
from io import BytesIO
import requests
from flask import Flask, render_template, request, make_response, send_file
from flask_restful import reqparse
from lxml import html

app = Flask(__name__)


@app.route("/")
def main_page():
    return render_template('cert_form.html')


@app.errorhandler(500)
def server_error(message):
    return render_template('err_page.html', error_message=message), 500


@app.route("/enroll", methods=['POST'])
def enroll():
    parser = reqparse.RequestParser()
    parser.add_argument('authority_select', location='form')
    parser.add_argument('authority_text', location='form')
    parser.add_argument('isProxy', location='form', help='Proxy protocol')
    parser.add_argument('proxy_protocol', location='form', help='Proxy protocol')
    parser.add_argument('proxy_address', location='form', help='Proxy address')
    parser.add_argument('proxy_port',  location='form', help='Proxy port')
    parser.add_argument('chain', location='form', help='Get p7b chain')
    parser.add_argument('base64', location='form', help='Get base64 encoded certificate or p7b chain')
    args = parser.parse_args()

    no_requests = [item.filename for item in request.files.getlist('request')
                   if os.path.splitext(item.filename)[1] != '.p10']

    if no_requests and no_requests != ['']:
        if len(no_requests) == 1:
            message = u'является файлом'
        else:
            message = u'являются файлами'
        raise ValueError(u'{} не {} запроса'.format(', '.join(no_requests), message))

    request_data = [item.read() for item in request.files.getlist('request')]

    if request_data == ['']:
        raise ValueError(u'Не указан(ы) файл(ы) запроса')

    s = BytesIO()
    temp_zip_file = zipfile.ZipFile(s, 'w')

    args['authority'] = args.get('authority_text') if args.get('authority_select') == u'Ввести свой адрес УЦ'\
        else args.get('authority_select')

    proxy = {args.get('proxy_protocol'): '{}:{}'.format(args.get('proxy_address'), args.get('proxy_port'))} \
        if args.get('isProxy') else None

    if args.get('isProxy') and not args.get('proxy_address') and not args.get('proxy_port'):
        raise ValueError(u'Адрес прокси указан неверно')

    i = 1

    for req in request_data:
        data = {'Mode': 'newreq',
                'CertRequest': req,
                'CertAttrib': 'UserAgent:Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
                'ThumbPrint': '',
                'TargetStoreFlags': '0',
                'SaveCert': 'yes'}

        certpage = requests.post('http://{}/certsrv/certfnsh.asp'
                                 .format(args.get('authority')), data=data, proxies=proxy, timeout=5)
        page = html.fromstring(certpage.content)
        srv, cert_bin, cert_b64, cert_chain_bin, cert_chain_b64 = page.xpath('//a/@href')

        if args.get('chain'):
            certificate_url = cert_chain_b64 if args.get('base64') else cert_chain_bin
        else:
            certificate_url = cert_b64 if args.get('base64') else cert_bin

        request_file = requests.get('http://{}/certsrv/{}'
                                    .format(args.get('authority'), certificate_url), proxies=proxy)

        file_format = 'p7b' if args.get('chain') else 'cer'

        if request_file.status_code == 200:
            if len(request_data) == 1:
                certificate = request_file.content
                response = make_response(certificate)
                response.headers["Content-Disposition"] = "attachment; filename=certnew.{}".format(file_format)
                return response
            else:
                data = zipfile.ZipInfo('certnew{}.{}'.format(i, file_format))
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                temp_zip_file.writestr(data, request_file.content)
                i += 1
        else:
            print "Bad certificate url"
            sys.exit(1)
    temp_zip_file.close()
    s.seek(0)
    return send_file(s, attachment_filename='certs.zip', as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
