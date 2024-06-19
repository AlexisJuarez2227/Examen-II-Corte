from flask import Flask, request, render_template_string
import re
import ply.lex as lex

app = Flask(__name__)

# Definición de tokens para el analizador léxico
tokens = [
    'PR', 'ID', 'NUM', 'SYM', 'ERR'
]

t_PR = r'\b(Inicio|cadena|proceso|si|ver|Fin)\b'
t_ID = r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
t_NUM = r'\b\d+\b'
t_SYM = r'[;{}()\[\]=<>!+-/*]'
t_ERR = r'.'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Plantilla HTML para mostrar resultados
html_template = '''
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap');
    body {
      font-family: 'Nunito', sans-serif;
      background-color: #f4f4f9;
      margin: 0;
      padding: 20px;
      color: #333;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .container {
      width: 100%;
      max-width: 1200px;
      background-color: #ffffff;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
    }
    .header {
      text-align: center;
      margin-bottom: 30px;
    }
    .header h1 {
      color: #2c3e50;
      margin: 0;
    }
    .header p {
      color: #7f8c8d;
      margin: 5px 0 0;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 20px;
      margin-bottom: 30px;
    }
    textarea {
      width: 100%;
      height: 150px;
      padding: 15px;
      border: 2px solid #bdc3c7;
      border-radius: 8px;
      font-size: 16px;
      resize: vertical;
      background-color: #ecf0f1;
      transition: border-color 0.3s;
    }
    textarea:focus {
      border-color: #3498db;
      outline: none;
    }
    .btn {
      background-color: #3498db;
      color: white;
      padding: 15px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.3s ease;
      font-size: 16px;
      align-self: flex-end;
      text-transform: uppercase;
    }
    .btn:hover {
      background-color: #2980b9;
    }
    .results {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
    }
    .card {
      background-color: #ecf0f1;
      flex: 1 1 calc(50% - 20px);
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s;
    }
    .card:hover {
      transform: translateY(-5px);
    }
    .card h2 {
      color: #3498db;
      margin-top: 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }
    th, td {
      padding: 15px;
      text-align: left;
      border-bottom: 2px solid #bdc3c7;
    }
    th {
      background-color: #3498db;
      color: white;
    }
    tr:nth-child(even) {
      background-color: #bdc3c7;
    }
    tr:hover {
      background-color: #ecf0f1;
    }
    .summary {
      font-weight: bold;
      background-color: #3498db;
      color: white;
    }
    .summary td {
      text-align: center;
    }
  </style>
  <title>Analizador Léxico y Sintáctico</title>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Analizador Léxico y Sintáctico</h1>
      <p>Ingrese su código para analizar</p>
    </div>
    <form method="post">
      <textarea name="code" rows="10">{{ code }}</textarea>
      <button type="submit" class="btn">Analizar</button>
    </form>
    <div class="results">
      <div class="card">
        <h2>Analizador Léxico</h2>
        <table>
          <thead>
            <tr>
              <th>Tokens</th><th>PR</th><th>ID</th><th>Números</th><th>Símbolos</th><th>Error</th>
            </tr>
          </thead>
          <tbody>
            {% for row in lexical %}
            <tr>
              <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td><td>{{ row[4] }}</td><td>{{ row[5] }}</td>
            </tr>
            {% endfor %}
            <tr class="summary">
              <td>Total</td><td>{{ total['PR'] }}</td><td>{{ total['ID'] }}</td><td>{{ total['NUM'] }}</td><td>{{ total['SYM'] }}</td><td>{{ total['ERR'] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <h2>Analizador Sintáctico y Semántico</h2>
        <table>
          <thead>
            <tr>
              <th>Sintáctico</th><th>Semántico</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ syntactic }}</td><td>{{ semantic }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</body>
</html>

'''

def analyze_lexical(code):
    lexer = lex.lex()
    lexer.input(code)
    results = {'PR': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'ERR': 0}
    rows = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        row = [''] * 6
        if tok.type in results:
            results[tok.type] += 1
            row[list(results.keys()).index(tok.type)] = 'x'
        rows.append(row)
    return rows, results

def analyze_syntactic(code):
    errors = []

    # Verificar la estructura de "Inicio" y "Fin"
    if not code.startswith("Inicio;"):
        errors.append("El código debe comenzar con 'Inicio;'.")
    if not code.endswith("Fin;"):
        errors.append("El código debe terminar con 'Fin;'.")

    # Verificar la estructura de bloques y sentencias
    if "proceso;" not in code:
        errors.append("Falta la declaración de 'proceso;'.")
    if "si (" in code and not re.search(r"si\s*\(.+\)\s*\{", code):
        errors.append("Estructura incorrecta de 'si'. Debe ser 'si (condición) {'.")
    if "{" in code and "}" not in code:
        errors.append("Falta cerrar un bloque con '}'.")
    if "}" in code and "{" not in code:
        errors.append("Falta abrir un bloque con '{'.")

    
    lines = code.split('\n')
    for i, line in enumerate(lines):
        # Ignorar líneas que no requieren punto y coma
        if line.strip() and not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().endswith('}') and "si (" not in line and "Inicio;" not in line and "Fin;" not in line:
            errors.append(f"Falta punto y coma al final de la línea {i + 1}.")

    if not errors:
        return "Sintaxis correcta"
    else:
        return " ".join(errors)

def analyze_semantic(code):
  errors = []
  variable_types = {}

  # Identificar y almacenar los tipos de las variables
  for var_declaration in re.findall(r"\b(cadena|entero)\s+'(\w+)'\s*=\s*(.*);", code):
    var_type, var_name, value = var_declaration
    variable_types[var_name] = var_type
    if var_type == "cadena" and not re.match(r'^".*"$', value):
      errors.append(f"Error semántico en la asignación de '{var_name}'. Debe ser una cadena entre comillas.")
    elif var_type == "entero" and not re.match(r'^\d+$', value):
      errors.append(f"Error semántico en la asignación de '{var_name}'. Debe ser un valor numérico.")

  # Verificar comparaciones lógicas
  logical_checks = re.findall(r"si\s*\((.+)\)", code)
  for check in logical_checks:
    match = re.search(r"(\w+)\s*(==|!=)\s*(\w+|\".*\"|\d+)", check)
    if match:
      left_var, _, right_var = match.groups()
      left_type = variable_types.get(left_var, None)
      right_type = 'cadena' if right_var.startswith('"') or not right_var.isdigit() else 'entero'
      if left_type and right_type and left_type != right_type:
        errors.append(f"Error semántico en la condición 'si ({check})'. No se puede comparar {left_type} con {right_type}.")

  if not errors:
    return "Uso correcto de las estructuras semánticas"
  else:
    return " ".join(errors)

@app.route('/', methods=['GET', 'POST'])
def index():
    code = ''
    lexical_results = []
    total_results = {'PR': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'ERR': 0}
    syntactic_result = ''
    semantic_result = ''
    if request.method == 'POST':
        code = request.form['code']
        lexical_results, total_results = analyze_lexical(code)
        syntactic_result = analyze_syntactic(code)
        semantic_result = analyze_semantic(code)
    return render_template_string(html_template, code=code, lexical=lexical_results, total=total_results, syntactic=syntactic_result, semantic=semantic_result)

if __name__ == '__main__':
    app.run(debug=True)