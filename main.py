import json
import mimetypes
import os
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from parser.parser import main_parser
import console.Console as Console
from parser.ParseError import ParseError
from console.Console import c_println

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

final_list = ""
cwd = "reportes"


@app.route('/ejecutar', methods=['POST'])
def main():
    with open("command_request.txt", "w") as file:
        file.write(request.json["commands"])

    command = "execute -path=command_request.txt"
    Console.clear()
    cmd = main_parser.parse(command)
    c_println("--------------------------------------------------------------------------------\n")
    cmd_return = cmd.run_command()
    c_println("Resultado del comando:" + str(cmd_return))

    response = {
        'console_output': Console.get_string(),
        'return_code': cmd_return
    }
    return jsonify(response)


@app.route('/lista_reportes', methods=['GET'])
def lista_reportes():
    global final_list, cwd
    final_list = ""
    cwd = "reportes"

    def print_file_path(directory, _files):
        global final_list, cwd
        for file in _files:
            final_list += os.path.join(".", directory, file).lstrip("./\\")[len(cwd):] + "\n"

    for root, a, files in os.walk(cwd):
        print_file_path(root, files)

    response = {
        'list': final_list.rstrip("\n"),
        'return_code': 0
    }
    return jsonify(response)


@app.route('/obtener_reporte', methods=['POST'])
def get_report():
    request_content = request.json
    print(request_content)

    file_path = os.path.join("./reportes", request_content["path"].lstrip("\\"))
    if not os.path.isfile(file_path):
        return "File not found", 404

    with open(file_path, "rb") as file:
        file_content = file.read()

    if file_path.endswith(".txt"):
        response_data = {
            "Content": file_content.decode('utf-8'),
            "ExitStatus": 200
        }
        return Response(json.dumps(response_data), content_type='application/json')

    mime_type, _ = mimetypes.guess_type(file_path)
    return Response(file_content, content_type=mime_type)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


def _main():
    print('MIA Proyecto. Ingrese algún comando')
    while True:
        try:
            command = input('mia> ')
        except EOFError:
            break
        if not command:
            continue
        if command == "exit":
            exit(0)
        Console.clear()

        ParseError.error = None
        cmd = main_parser.parse(command)
        if ParseError.error is not None:
            c_println(f"Error en el comando.")
            continue
        c_println("--------------------------------------------------------------------------------\n")
        cmd_return = cmd.run_command()
        c_println("Resultado del comando:" + str(cmd_return))
