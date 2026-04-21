import json
from flask import Flask, abort, send_file
from os import path, environ

app = Flask(__name__)

base_dir = environ.get('BASE_DIR', path.dirname(path.abspath(__file__)))

@app.route('/.well-known/terraform.json', methods=['GET'])
def discovery():
    return {"providers.v1": "/v1/providers/"}

@app.route('/v1/providers/<namespace>/<name>/versions', methods=['GET'])
def versions(namespace, name):
    filepath = path.join(base_dir, 'providers/' + namespace + "/" + name + ".json")

    if not path.exists(filepath):
        abort(404)

    with open(filepath) as reader:
        data = json.load(reader)

    response = { "versions" : [] }

    for elem in data["versions"]:
        version = {"version": elem["version"], "protocols": elem["protocols"], "platforms": []}

        for platform in elem["platforms"]:
            version["platforms"].append({"os": platform["os"], "arch": platform["arch"]})

        response["versions"].append(version)
    
    return response

@app.route('/v1/providers/<namespace>/<name>/<version>/download/<os>/<arch>', methods=['GET'])
def package(namespace, name, version, os, arch):
    filepath = path.join(base_dir, 'providers/' + namespace + "/" + name + ".json")

    if not path.exists(filepath):
        abort(404)

    with open(filepath) as reader:
        data = json.load(reader)

    provider = None

    for elem in data["versions"]:
        if elem["version"] == version:
            for platform in elem["platforms"]:
                if platform["os"] == os and platform["arch"] == arch:
                    provider = platform
                    provider["protocols"] = elem["protocols"]
    
    if provider is None:
        abort(404)

    return provider

@app.route('/downloads/<namespace>/<name>/<version>/<os>/<arch>')
def download_zip(namespace, name, version, os, arch):
    filepath = path.join(base_dir, 'providers/' + namespace + "/" + name + ".json")

    if not path.exists(filepath):
        abort(404)

    with open(filepath) as reader:
        data = json.load(reader)

    filename = None
    for elem in data["versions"]:
        if elem["version"] == version:
            for platform in elem["platforms"]:
                if platform["os"] == os and platform["arch"] == arch:
                    filename = platform["filename"]
                    break
            break

    if filename is None:
        abort(404)

    zip_filepath = path.join(base_dir, 'downloads', namespace, name, version, os, arch, filename)

    if not path.exists(zip_filepath):
        abort(404)

    return send_file(zip_filepath)

@app.route('/v1/providers/<namespace>/<name>/<version>/shasums', methods=['GET'])
def shasums(namespace, name, version):
    filepath = path.join(base_dir, 'downloads', namespace, name, version, 'SHA256SUMS')

    if not path.exists(filepath):
        abort(404)

    return send_file(filepath, mimetype='text/plain')

@app.route('/v1/providers/<namespace>/<name>/<version>/shasums.sig', methods=['GET'])
def shasums_sig(namespace, name, version):
    filepath = path.join(base_dir, 'downloads', namespace, name, version, 'SHA256SUMS.sig')

    if not path.exists(filepath):
        abort(404)

    return send_file(filepath, mimetype='application/octet-stream')

@app.route('/')
def home():
    return 'Rekistry (Simple terraform private/local registry)'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)