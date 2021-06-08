from app import db
from requests import post, get, delete, put
from requests.exceptions import RequestException
from urllib.parse import urljoin
from xml.etree import ElementTree

_REST_API_URL = 'https://app.ecwid.com/api/v3/{store_id}/{endpoint}'
_PARTNERS_API_URL = 'https://my.ecwid.com/resellerapi/v1/'
_OAUTH_URL = 'https://my.ecwid.com/api/oauth/token/'
_DEFAULT_STORE_PROFILE = {'languages':{'enabledLanguages': ['ru'], 'defaultLanguage': 'ru'},
						  'formatsAndUnits':{'currency':'RUB', 'currencyPrefix':'', 'currencySuffix':'₽',
						  'weightUnit':'KILOGRAM', 'dateFormat':'dd-MM-yyyy', 'timezone':'Europe/Moscow',
						  'timeFormat': 'HH:mm:ss', 'dimensionsUnit':'CM'}}
						  
class EcwidAPIException(Exception):
	pass

class EcwidAPI():
	id  = db.Column(db.Integer, primary_key=True)
	partners_key = db.Column(db.String(128))
	client_id = db.Column(db.String(128))
	client_secret = db.Column(db.String(128))
	token = db.Column(db.String(128))
	name = db.Column(db.String(128))
	email = db.Column(db.String(128))
	url = db.Column(db.String())

	def GetStoreToken(self):
		'''Gets store token using REST API, returns JSON'''
		payload = {'client_id':self.client_id, 'client_secret':self.client_secret, 'grant_type':'authorization_code'}
		try:
			response = post(urljoin(_OAUTH_URL, str(self.id)), data = payload)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException('Неизвестная ошибка API.')
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if 'access_token' not in json:
			raise EcwidAPIException('Не удалось получить токен доступа к магазину {}.'.format(self.id))
		self.token = json['access_token']
		return json

	def GetStoreEndpoint(self, endpoint, **kwargs):
		'''Gets store's endpoint using REST API, returns JSON'''
		params = {'token':self.token, **kwargs}
		try:
			response = get(_REST_API_URL.format(store_id = self.id,endpoint = endpoint), params = params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException(self._GetErrorMessage(response.status_code))
		try:
			result = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if all([k in result for k in ['count', 'total', 'items']]):
			received = result['count']
			while received < result['total']:
				params['offset'] = received
				try:
					response = get(_REST_API_URL.format(store_id = self.id,endpoint = endpoint), params = params)
				except RequestException:
					raise EcwidAPIException('Ошибка обращения по API.')
				if response.status_code != 200:
					raise EcwidAPIException(self._GetErrorMessage(response.status_code))
				try:
					next = response.json()
				except ValueError:
					raise EcwidAPIException('Ошибка обращения по API.')
				if not all([k in next for k in ['count', 'total', 'items']]):
					break
				received += next['count']
				result['items'] += next['items']
			result['total'] = received
			result['count'] = received
		return result

	def GetStoreOrders(self, **kwargs):
		'''Gets store's orders using REST API, returns JSON'''
		return self.GetStoreEndpoint('orders', **kwargs)

	def _GetErrorMessage(self, error):
		if error == 400:
			message = 'Неверные параметры запроса.'
		elif error == 402 or error == 403:
			message = 'Недостаточно прав на выполнение запроса.'
		elif error == 404:
			message = 'Пользователь, магазин или товар не найден.'
		elif error == 409:
			message = 'Значения полей товара не верные.'
		elif error == 415 or error == 422:
			message = 'Неверный тип запроса.'
		elif error != 200:
			message = 'Неизвестная ошибка API.'
		return '{}: {}'.format(error, message)

	def DeleteStoreOrder(self, order_id):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		try:
			response = delete(_REST_API_URL.format(store_id = self.id,endpoint = 'orders/{}'.format(order_id)), params = params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException(self._GetErrorMessage(response.status_code))
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if json.get('deleteCount', 0) == 0:
			raise EcwidAPIException('Не удалось удалить заявку {}.'.format(order_id))
		return json

	def UpdateStoreOrder(self, order_id, order):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		try:
			response = put(_REST_API_URL.format(store_id = self.id,endpoint = 'orders/{}'.format(order_id)), params = params, json = order)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException(self._GetErrorMessage(response.status_code))
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if json.get('updateCount', 0) == 0:
			raise EcwidAPIException('Не удалось обновить заявку {}.'.format(order_id))
		return json
		
	def OrderInvoice(self, order_id):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		try:
			response = get(_REST_API_URL.format(store_id = self.id,endpoint = 'orders/{}/invoice'.format(order_id)), params = params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException(self._GetErrorMessage(response.status_code))
		return response.text
		
	def CreateStore(self, name, email, password, plan, **kwargs):
		'''Create store using Partners API, returns store_id'''
		payload = {'name':name, 'email':email, 'password':password, 'plan':plan, 'key':self.partners_key, **kwargs}
		params = {'register':'y'}
		try:
			response = post(urljoin(_PARTNERS_API_URL, 'register'), data = payload, params = params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code == 409:
			raise EcwidAPIException('Электронный адрес уже используется.')
		elif response.status_code == 400:
			raise EcwidAPIException('Некорретный электронный адрес.')
		elif response.status_code == 403:
			raise EcwidAPIException('Некорретный ключ partners_key.')
		elif response.status_code == 405:
			raise EcwidAPIException('Некорректный HTTP метод.')
		elif response.status_code != 200:
			raise EcwidAPIException('Неизвестная ошибка API.')
		xml = ElementTree.fromstring(response.text)
		return int(xml.text)
		
	def DeleteStore(self):
		'''Removes store using Partners API, returns Boolean'''
		payload = {'ownerid':self.id, 'key':self.partners_key}
		try:
			response = post(urljoin(_PARTNERS_API_URL, 'delete'), data = payload)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code == 403:
			raise EcwidAPIException('Недостаточно прав на удаление поставщика {}.'.format(self.id))
		elif response.status_code != 200:
			raise EcwidAPIException('Неизвестная ошибка API.')

	def GetStoreProfile(self, **kwargs):
		'''Gets store profile using REST API, returns JSON'''
		json = self.GetStoreEndpoint('profile', **kwargs)
		try:
			self.name = json['account']['accountName']
			self.name = json['account']['accountEmail']
			db.session.commit()
		except (KeyError, TypeError):
			raise EcwidAPIException('Ошибка обращения по API.')
		return json
		
	def GetStoreProducts(self, **kwargs):
		'''Gets store profile using REST API, returns JSON'''
		return self.GetStoreEndpoint('products', **kwargs)
		
	def UpdateStoreProfile(self, template = None):
		'''Updates store profile using REST API, returns JSON'''
		params = {'token':self.token}
		if template is None:
			template = _DEFAULT_STORE_PROFILE
		else:
			template =  {**template, **_DEFAULT_STORE_PROFILE}
		try:
			response = put(_REST_API_URL.format(store_id=self.id, endpoint='profile'), json=template, params=params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise EcwidAPIException(self._GetErrorMessage(response.status_code))
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if json.get('updateCount', 0) == 0:
			raise EcwidAPIException('Не удалось обновить профиль поставщика {}.'.format(self.id))
		return json
		
	def SetStoreOrder(self, order):
		'''Sets store's order using REST API, returns JSON'''
		params = {'token':self.token}
		try:
			response = post(_REST_API_URL.format(store_id = self.id, endpoint = 'orders'), json = order, params=params)
		except RequestException:
			raise EcwidAPIException('Ошибка обращения по API.')
		if response.status_code != 200:
			raise Exception(self._GetErrorMessage(response.status_code))
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if json.get('id', 0) == 0:
			raise EcwidAPIException('Не удалось создать заявку.')
		return json
		
	def DeleteStoreProduct(self, product_id):
		'''Deletes store's product using REST API, returns JSON'''
		params = {'token':self.token}
		response = delete(_REST_API_URL.format(store_id = self.id, endpoint = 'products/{}'.format(product_id)), params = params)
		if response.status_code != 200:
			raise Exception(self._GetErrorMessage(response.status_code))
		try:
			json = response.json()
		except ValueError:
			raise EcwidAPIException('Ошибка обращения по API.')
		if json.get('deleteCount', 0) == 0:
			raise EcwidAPIException('Не удалось удалить товар {}.'.format(product_id))
		return json