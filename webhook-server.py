#!/usr/bin/env python3
"""
Простой и надежный Webhook сервер для автоматического деплоя Catty Reminders
"""

import json
import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Конфигурация
PORT = 8080
APP_DIR = "/home/alex/catty-reminders-app"
DEPLOY_SCRIPT = "/home/alex/deploy.sh"

class WebhookHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Кастомное логирование запросов"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📡 [{timestamp}] {format % args}")
    
    def do_GET(self):
        """Обработка GET запросов - страница статуса"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = f"""
        <html>
        <head><title>Catty Reminders Webhook</title></head>
        <body>
            <h1>🚀 Catty Reminders Webhook Server</h1>
            <p><strong>Status:</strong> 🟢 Active</p>
            <p><strong>Port:</strong> {PORT}</p>
            <p><strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Send POST request with GitHub webhook payload to trigger deployment.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Обработка POST запросов от GitHub"""
        try:
            # Читаем данные
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            print("🎯 POST запрос получен")
            print(f"   Content-Length: {content_length}")
            
            # Парсим JSON
            payload = json.loads(body.decode('utf-8'))
            event_type = self.headers.get('X-GitHub-Event', 'unknown')
            
            print(f"🔔 GitHub Event: {event_type}")
            print(f"📦 Репозиторий: {payload.get('repository', {}).get('full_name', 'unknown')}")
            
            # Обрабатываем только push события
            if event_type == 'push':
                self.handle_push_event(payload)
            else:
                print(f"ℹ️  Игнорируем событие: {event_type}")
            
            # Всегда отвечаем 200
            self.send_success_response()
            
        except Exception as e:
            print(f"❌ Ошибка обработки POST: {e}")
            self.send_error_response(500, str(e))
    
    def handle_push_event(self, payload):
        """Обработка push события - основной CI/CD пайплайн"""
        print("🚀 НАЧИНАЕМ ОБРАБОТКУ PUSH EVENT")
        
        branch = payload.get('ref', '').replace('refs/heads/', '')
        clone_url = payload.get('repository', {}).get('clone_url', '')
        commits_count = len(payload.get('commits', []))
        
        print(f"   Ветка: {branch}")
        print(f"   Коммитов: {commits_count}")
        print(f"   Clone URL: {clone_url}")
        
        # Шаг 1: Запускаем тесты
        if self.run_tests():
            # Шаг 2: Если тесты прошли - деплоим
            self.run_deployment()
        else:
            print("❌ Тесты не пройдены, деплой отменен")
    
    def run_tests(self):
        """Запуск тестов приложения"""
        print("🧪 ЗАПУСКАЕМ ТЕСТЫ...")
        
        test_files = [
            ("Unit тесты", "test_unit.py"),
            ("API тесты", "test_api.py"), 
            # ("UI тесты", "test_ui.py")
        ]
        
        all_passed = True
        
        for test_name, test_file in test_files:
            test_path = os.path.join(APP_DIR, "tests", test_file)
            
            if not os.path.exists(test_path):
                print(f"   ⚠️  {test_name}: файл не найден - {test_path}")
                continue
            
            print(f"   🔍 Запускаем {test_name}...")
            
            try:
                result = subprocess.run(
                    ["python3", "-m", "pytest", test_path, "-v"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {test_name}: ПРОЙДЕНЫ")
                else:
                    print(f"   ❌ {test_name}: ПРОВАЛЕНЫ")
                    print(f"      Ошибка: {result.stderr[:200]}...")
                    all_passed = False
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ {test_name}: ТАЙМАУТ")
                all_passed = False
            except Exception as e:
                print(f"   💥 {test_name}: ОШИБКА - {e}")
                all_passed = False
        
        return all_passed
    
    def run_deployment(self):
        """Запуск скрипта деплоя"""
        print("🚀 ЗАПУСКАЕМ ДЕПЛОЙ...")
        
        if not os.path.exists(DEPLOY_SCRIPT):
            print(f"❌ Скрипт деплоя не найден: {DEPLOY_SCRIPT}")
            return False
        
        try:
            result = subprocess.run(
                ["/bin/bash", DEPLOY_SCRIPT],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ ДЕПЛОЙ УСПЕШНО ЗАВЕРШЕН!")
                print(f"   Вывод: {result.stdout}")
                return True
            else:
                print("❌ ОШИБКА ДЕПЛОЯ!")
                print(f"   Код ошибки: {result.returncode}")
                print(f"   Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ ТАЙМАУТ ДЕПЛОЯ!")
            return False
        except Exception as e:
            print(f"💥 ОШИБКА ПРИ ДЕПЛОЕ: {e}")
            return False
    
    def send_success_response(self):
        """Отправка успешного ответа"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "success", "message": "Webhook processed"}')
    
    def send_error_response(self, code, message):
        """Отправка ответа с ошибкой"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = json.dumps({"status": "error", "message": message})
        self.wfile.write(error_response.encode('utf-8'))

def main():
    """Запуск сервера"""
    print("🚀 Запуск Catty Reminders Webhook Server")
    print(f"📍 Порт: {PORT}")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 App directory: {APP_DIR}")
    print(f"🔧 Deploy script: {DEPLOY_SCRIPT}")
    print("\n👂 Ожидаем webhook запросы...\n")
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")

if __name__ == '__main__':
    main()
