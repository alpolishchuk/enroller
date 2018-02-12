# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import re
import sys
import time
import zipfile
from io import BytesIO

import requests
from flask import Flask, render_template, request, make_response, send_file, Response
from flask_restful import reqparse
from lxml import html

app = Flask(__name__)


@app.route("/")
def main_page():
    return render_template('cert_form.html')


@app.errorhandler(400)
def server_error(message):
    return render_template('err_page.html', error_message=message), 400


@app.errorhandler(500)
def internal_error(message):
    return render_template('server_err_page.html', server_message=message), 500


@app.route("/enroll", methods=['POST'])
def enroll():
    parser = reqparse.RequestParser()
    parser.add_argument('authority_select', location='form')
    parser.add_argument('authority_text', location='form')
    parser.add_argument('is_proxy', location='form', help='Proxy protocol')
    parser.add_argument('proxy_protocol', location='form', help='Proxy protocol')
    parser.add_argument('proxy_address', location='form', help='Proxy address')
    parser.add_argument('proxy_port', location='form', help='Proxy port')
    parser.add_argument('chain', location='form', help='Get p7b chain')
    parser.add_argument('base64', location='form', help='Get base64 encoded certificate or p7b chain')
    args = parser.parse_args()

    proxy = None

    if not (args.get('authority_select') or args.get('authority_text')) and not request.files.getlist('request'):
        return Response(response='Некорректный запрос', status=400)

    if not (args.get('authority_select') or args.get('authority_text')):
        return Response(response='Не указан адрес УЦ', status=400)

    no_requests = [item.filename for item in request.files.getlist('request')
                   if os.path.splitext(item.filename)[1] != '.p10']

    if no_requests and no_requests != ['']:
        if len(no_requests) == 1:
            message = 'является файлом'
        else:
            message = 'являются файлами'
        return Response(response='{} не {} запроса'.format(', '.join(no_requests), message), status=400)

    request_data = [item.read() for item in request.files.getlist('request')]

    if not request_data or not any(request_data):
        return Response(response='Не указан(ы) файл(ы) запроса', status=400)

    if args.get('authority_select') == 'Ввести свой адрес УЦ':
        authority = args.get('authority_text')
    else:
        authority = args.get('authority_select')

    if args.get('is_proxy'):
        if not (args.get('proxy_address')
                and args.get('proxy_port')
                and re.compile(r'^\d{,5}$').match(args.get('proxy_port'))
                and 0 < int(args.get('proxy_port')) < 65536
                and isinstance(args.get('proxy_port'), str)):
            return Response(response='Адрес прокси указан неверно', status=400)

        proxy = {args.get('proxy_protocol'): '{}:{}'.format(args.get('proxy_address'), args.get('proxy_port'))}

    s = BytesIO()
    temp_zip_file = zipfile.ZipFile(s, 'w')

    for req in request_data:
        data = {'Mode': 'newreq',
                'CertRequest': req,
                'CertAttrib': 'UserAgent:Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
                'ThumbPrint': '',
                'TargetStoreFlags': '0',
                'SaveCert': 'yes'}

        certpage = requests.post(
            'http://{}/certsrv/certfnsh.asp'.format(authority), data=data, proxies=proxy, timeout=5
        )
        page = html.fromstring(certpage.content)
        try:
            srv, cert_bin, *rest_options = page.xpath('//a/@href')
            certificate_url = cert_bin
            if rest_options:
                cert_b64, cert_chain_bin, cert_chain_b64 = rest_options

                if args.get('base64'):
                    certificate_url = cert_chain_b64 if args.get('chain') else cert_b64
                else:
                    certificate_url = cert_chain_bin if args.get('chain') else cert_bin
        except ValueError:
            err_title = page.xpath("//p[@id = 'locDenied']")
            error_title = err_title[0].text.strip() if err_title else 'Неизвестная ошибка.'
            err_text = page.xpath("//p[@id = 'locInfoReqIDandReason']")
            error_text = err_text[0].text.strip() if err_text else 'Ошибка создания сертификата.'
            error_message = '\n'.join([error_title, error_text])
            return Response(response=error_message, status=400)

        request_file = requests.get(
            'http://{}/certsrv/{}'.format(authority, certificate_url), proxies=proxy
        )

        file_format = 'p7b' if args.get('chain') else 'cer'
        if request_file.status_code == 200:
            if len(request_data) == 1:
                certificate = request_file.content
                response = make_response(certificate)
                response.headers["Content-Disposition"] = "attachment; filename=certnew.{}".format(file_format)
                return response
            else:
                data = zipfile.ZipInfo('certnew{}.{}'.format(request_data.index(req) + 1, file_format))
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                temp_zip_file.writestr(data, request_file.content)
        else:
            print ("Bad certificate url")
            sys.exit(1)
    temp_zip_file.close()
    s.seek(0)
    return send_file(s, attachment_filename='certs.zip', as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
