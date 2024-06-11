from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
from pyzbar import pyzbar
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Словарь штрихкодов и названий продуктов
barcodes = {
    "4603934000793": 'Вода "Святой источник"',
    # Добавьте другие штрих-коды и соответствующие им названия продуктов здесь
}

# Словарь для хранения количества продуктов в холодильнике
fridge = {}

# Время ожидания после успешного сканирования, чтобы избежать двойного сканирования
WAIT_TIME = 5  # секунды
last_scanned = {}


# Функция для распознавания штрихкодов и DataMatrix
def decode_barcode(image):
    barcodes = pyzbar.decode(image)
    return barcodes


# Функция для получения названия продукта по штрихкоду
def get_product_name(barcode):
    return barcodes.get(barcode, "Product name not found")


# Открытие видеопотока с камеры
def scan_barcode():
    fridge = {'123': 1}
    time.sleep(5)
    print(123)
    socketio.emit('update_fridge', {'fridge': fridge})

    cap = cv2.VideoCapture(1)  # 0 - индекс камеры, может быть изменен на другой, если у вас несколько камер

    if not cap.isOpened():
        print("Ошибка: не удается открыть камеру")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Ошибка: не удается получить кадр")
            break

        # Распознавание штрихкодов и DataMatrix на кадре
        barcodes_detected = decode_barcode(frame)

        current_time = time.time()
        for barcode in barcodes_detected:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type

            # Проверяем, прошло ли достаточно времени с последнего сканирования этого штрих-кода
            if barcode_data in last_scanned and current_time - last_scanned[barcode_data] < WAIT_TIME:
                continue

            last_scanned[barcode_data] = current_time
            print(f"Detected {barcode_type}: {barcode_data}")

            # Получение названия продукта по штрихкоду
            product_name = get_product_name(barcode_data)
            print("Название продукта:")
            print(product_name)

            # Обновление количества продукта в холодильнике
            if product_name in fridge:
                fridge[product_name] += 1
            else:
                fridge[product_name] = 1

            print(f"Продукт '{product_name}' обновлен в холодильнике. Количество: {fridge[product_name]}")
            print(fridge)

            # Послать обновленное состояние холодильника клиенту
            socketio.emit('update_fridge', {'fridge': fridge})

            # Рисуем прямоугольник вокруг штрих-кода
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Добавляем текст с данными штрихкода и названием продукта
            text = f"{barcode_data} ({barcode_type}): {product_name}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Camera', frame)

        # Выход из цикла по нажатию клавиши 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    scan_thread = threading.Thread(target=scan_barcode)
    scan_thread.daemon = True
    scan_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
