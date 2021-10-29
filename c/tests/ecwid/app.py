import flask
import json
from flask import request


app = flask.Flask(__name__)


@app.route('/api/v3/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index():
    return flask.jsonify({'key': 'value'})


@app.route('/api/v3/<int:store_id>/<endpoint>/<int:resource_id>',
           methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/api/v3/<int:store_id>/<endpoint>',
           methods=['GET', 'POST', 'PUT', 'DELETE'],
           defaults={'resource_id': None})
def endpoint(store_id, endpoint, resource_id):
    with open(
        f'tests/ecwid/jsons/{flask.request.method}-{endpoint}{store_id}.json',
        mode='r',
        encoding='utf-8'
    ) as f:
        result = json.load(f)

    if endpoint == 'categories' and request.args.get('parent', 0, type=int) == 1:
        result['count'] = 0
        result['total'] = 0
        result['items'] = list()

    result['offset'] = request.args.get('offset', 0, type=int)
    return flask.jsonify(result)


@app.route('/api/v3/<int:store_id>/products/<int:product_id>/image',
           methods=['POST'])
def image(store_id, product_id):
    with open(
        f'tests/ecwid/jsons/POST-image{store_id}.json',
        mode='r',
        encoding='utf-8'
    ) as f:
        result = json.load(f)
    return flask.jsonify(result)


if __name__ == "__main__":
    app.run()
