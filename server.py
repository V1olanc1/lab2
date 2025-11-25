from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Тестовый сервер СНИЛС</title>
    </head>
    <body>
        <h1>Тестовая база сотрудников</h1>

        <h2>Сотрудники:</h2>
        <ul>
            <li>Иванов Иван - СНИЛС: <b>112-233-445 95</b></li>
            <li>Петров Петр - СНИЛС: <b>156-789-123 07</b></li>
            <li>Сидорова Анна - СНИЛС: <b>234-567-890 12</b></li>
        </ul>

        <h2>Контакты:</h2>
        <p>Телефон: 123-456-789 (это не СНИЛС)</p>
        <p>Невалидный СНИЛС: 999-888-777 00</p>
    </body>
    </html>
    """


@app.route('/employees')
def employees():
    return """
    <h1>Страница сотрудников</h1>
    <p>СНИЛС сотрудников:</p>
    <ul>
        <li>112-233-445 95</li>
        <li>156-789-123 07</li>
        <li>234-567-890 12</li>
    </ul>
    """


if __name__ == '__main__':
    app.run()