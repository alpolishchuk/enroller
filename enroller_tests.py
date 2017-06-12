# -*- coding: utf-8 -*-
import enroller
import unittest
from io import BytesIO
from flask.testing import FlaskClient


class CustomClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        self._content_type = kwargs.pop("content_type")
        super(CustomClient, self).__init__(*args, **kwargs)


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        enroller.app.test_client_class = CustomClient
        enroller.app.config['TESTING'] = True
        self.app = enroller.app.test_client(content_type='multipart/form-data')

    def test_empty_request(self):
        response = self.app.post("/enroll")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Некорректный запрос')

    def test_no_authority(self):
        response = self.app.post("/enroll", data=dict(request=(BytesIO('my file contents'), 'hello world.txt')))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Не указан адрес УЦ')

    def test_no_request_file(self):
        response = self.app.post("/enroll", data={'authority_select': '1.1.1.1'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Не указан(ы) файл(ы) запроса')

    def test_invalid_request_file(self):
        file_name = '1.txt'
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=(BytesIO('file content'), file_name)))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, '{} не является файлом запроса'.format(file_name))
        
    def test_invalid_with_valid_request_file(self):
        req_name = '1.p10'
        file_name1 = '1.txt'
        file_name2 = '2.txt'
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=[(BytesIO('req content'), req_name),
                                                               (BytesIO('file content'), file_name1)]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, '{} не является файлом запроса'.format(file_name1))
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=[(BytesIO('req content'), req_name),
                                                               (BytesIO('file content'), file_name1),
                                                               (BytesIO('file content'), file_name2)]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, '{}, {} не являются файлами запроса'.format(file_name1, file_name2))

    def test_set_proxy(self):
        req_name = '1.p10'
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=(BytesIO('req content'), req_name),
                                                      isProxy=True))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Адрес прокси указан неверно')
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=(BytesIO('req content'), req_name),
                                                      isProxy=True,
                                                      proxy_address='1.2.3.4'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Адрес прокси указан неверно')
        response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                      request=(BytesIO('req content'), req_name),
                                                      isProxy=True,
                                                      proxy_port='8000'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Адрес прокси указан неверно')
        ports = ['as', '2v', '0', 8080, '65536', '123456']
        for item in ports:
            response = self.app.post("/enroll", data=dict(authority_select='1.1.1.1',
                                                          request=(BytesIO('req content'), req_name),
                                                          isProxy=True,
                                                          proxy_address='1.2.3.4',
                                                          proxy_port=item))
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data, 'Адрес прокси указан неверно')

if __name__ == '__main__':
    unittest.main()
