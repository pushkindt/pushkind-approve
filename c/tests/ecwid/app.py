import flask
import json


app = flask.Flask(__name__)


@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index():
    return flask.jsonify({'key': 'value'})


@app.route('/api/v3/<int:store_id>/<endpoint>',
           methods=['GET', 'POST', 'PUT', 'DELETE'])
def endpoint(store_id, endpoint):
    with open(
        f'jsons/{flask.request.method}-{endpoint}.json',
        'r',
        encoding='utf-8'
    ) as f:
        result = json.load(f)
    return flask.jsonify(result)


@app.route('/api/v3/<int:store_id>/products/<int:product_id>/image',
           methods=['POST'])
def image(store_id, product_id):
    with open('jsons/POST-image.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    return flask.jsonify(result)


if __name__ == "__main__":
    app.run()
