# StudyFlow — Python + Flask

## Запуск (Windows / macOS / Linux)
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Відкрийте http://127.0.0.1:5000

Завдання та налаштування зберігаються локально у `study_data.json`.

MVP: завдання CRUD, виконані/невиконані, автоматичний підбір за порядком, два таймери, pause/resume/stop, результат, базові нагадування.

Прототипні обмеження: активна сесія не зберігається після перезавантаження сторінки; «Продовжити» після таймера задачі додає 5 хвилин; звук — короткий сигнал браузера, системні notifications доступні за дозволом браузера.
