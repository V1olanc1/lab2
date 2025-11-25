from flask import Flask

app = Flask(__name__)


@app.route('/')
def snils_list():
    return """
    <html>
    <head><title>СНИЛС примеры</title></head>
    <body>
        <h1>Примеры СНИЛС</h1>

        <h2>Правильные СНИЛС:</h2>
        <ul>
            <li>112-233-445 95</li>
            <li>123-456-789 01</li>
            <li>087-654-303 00</li>
            <li>156-789-123 45</li>
            <li>11223344595</li>
        </ul>

        <h2>Неправильные СНИЛС:</h2>
        <ul>
            <li>123-456-789 00</li>
            <li>112233445</li>
            <li>abc-def-ghi jk</li>
            <li>000-000-000 00</li>
            <li>123456789</li>
        </ul>
    </body>
    </html>
    """


if __name__ == '__main__':
    app.run()