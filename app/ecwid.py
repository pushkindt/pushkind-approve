from app import db
from requests import post, get, delete, put
from urllib.parse import urljoin

_REST_API_URL = 'https://app.ecwid.com/api/v3/{store_id}/{endpoint}'
_PARTNERS_API_URL = 'https://my.ecwid.com/resellerapi/v1/'
_OAUTH_URL = 'https://my.ecwid.com/api/oauth/token/'

class EcwidAPIException(Exception):
	pass

class EcwidAPI():
	partners_key = db.Column(db.String(128))
	client_id = db.Column(db.String(128))
	client_secret = db.Column(db.String(128))
	store_id = db.Column(db.Integer, unique = True)
	token = db.Column(db.String(128))

	def EcwidGetStoreToken(self):
		'''Gets store token using REST API, returns JSON'''
		payload = {'client_id':self.client_id, 'client_secret':self.client_secret, 'grant_type':'authorization_code'}
		response = post(urljoin(_OAUTH_URL, str(self.store_id)), data = payload)
		if response.status_code != 200:
			raise EcwidAPIException('Неизвестная ошибка API.')
		json = response.json()
		if 'access_token' not in json:
			raise EcwidAPIException('Не удалось получить доступ к магазину.')
		self.token = json['access_token']
		return json

	def EcwidGetStoreEndpoint(self, endpoint, **kwargs):
		'''Gets store's endpoint using REST API, returns JSON'''
		params = {'token':self.token, **kwargs}
		response = get(_REST_API_URL.format(store_id = self.store_id,endpoint = endpoint), params = params)
		if response.status_code != 200:
			raise EcwidAPIException(self._EcwidGetErrorMessage(response.status_code))
		result = response.json()
		if all([k in result for k in ['count', 'total', 'items']]):
			received = result['count']
			while received < result['total']:
				params['offset'] = received
				response = get(_REST_API_URL.format(store_id = self.store_id,endpoint = endpoint), params = params)
				if response.status_code != 200:
					raise EcwidAPIException(self._EcwidGetErrorMessage(response.status_code))
				next = response.json()
				if not all([k in next for k in ['count', 'total', 'items']]):
					break
				received += next['count']
				result['items'] += next['items']
			result['total'] = received
			result['count'] = received
		return result

	def EcwidGetStoreOrders(self, **kwargs):
		'''Gets store's orders using REST API, returns JSON'''
		return self.EcwidGetStoreEndpoint('orders', **kwargs)

	def _EcwidGetErrorMessage(self, error):
		if error == 400:
			message = 'Неверные параметры запроса.'
		elif error == 402 or error == 403:
			message = 'Недостаточно прав на выполнение запроса.'
		elif error == 404:
			message = 'Пользователь, магазин или товар не найден.'
		elif error == 409:
			message = 'Значения полей товара не верные.'
		elif error == 415 or error == 422:
			message = 'Неверные тип запроса.'
		elif error != 200:
			message = 'Неизвестная ошибка API.'
		return '{}: {}'.format(error, message)

	def EcwidDeleteStoreOrder(self, order_id):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		response = delete(_REST_API_URL.format(store_id = self.store_id,endpoint = 'orders/{}'.format(order_id)), params = params)
		if response.status_code != 200:
			raise EcwidAPIException(self._EcwidGetErrorMessage(response.status_code))
		return response.json()

	def EcwidUpdateStoreOrder(self, order_id, order):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		response = put(_REST_API_URL.format(store_id = self.store_id,endpoint = 'orders/{}'.format(order_id)), params = params, json = order)
		if response.status_code != 200:
			raise EcwidAPIException(self._EcwidGetErrorMessage(response.status_code))
		return response.json()
		
	def EcwidOrderInvoice(self, order_id):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		response = get(_REST_API_URL.format(store_id = self.store_id,endpoint = 'orders/{}/invoice'.format(order_id)), params = params)
		if response.status_code != 200:
			raise EcwidAPIException(self._EcwidGetErrorMessage(response.status_code))
		return response.text	