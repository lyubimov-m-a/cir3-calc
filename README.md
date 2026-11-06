# Калькуляторы прогноза при циррозе печени

Три самостоятельных приложения на Python + PyQt6.

| Папка     | Модель                             | Выход                            | Порог |
| --------- | ---------------------------------- | -------------------------------- | ----- |
| `model1/` | Летальность до 6 месяцев           | Вероятность летального исхода, % | 2.04% |
| `model2/` | Безрецидивная выживаемость         | Риск летального исхода, %        | 88.8% |
| `model3/` | Бестрансплантационная выживаемость | Риск летального исхода, %        | 74.5% |

Каждая папка содержит самостоятельное приложение со своим `main.py`,
`const.py`, стилями, иконкой, лицензией, `build.bat` и тестами.

## Исполняемые файлы для Windows 10+

1: [<img width="123" height="123" alt="qr1" src="https://github.com/user-attachments/assets/b0253853-a90c-4d21-8f44-f312a94312df" />](https://github.com/lyubimov-m-a/cir3-calc/releases/latest/download/model1.exe)
2: [<img width="123" height="123" alt="qr2" src="https://github.com/user-attachments/assets/94834a0c-c0a6-43a8-a8d1-f4def878111f" />](https://github.com/lyubimov-m-a/cir3-calc/releases/latest/download/model2.exe)
3: [<img width="123" height="123" alt="qr3" src="https://github.com/user-attachments/assets/1b57b97d-bba2-4a1c-aeba-7388f5968821" />](https://github.com/lyubimov-m-a/cir3-calc/releases/latest/download/model3.exe)

## Быстрый запуск

```bash
cd model1  # или model2, model3
pip install -r requirements.txt
python main.py
```

## Проверка

```bash
cd model1
python -m unittest discover -s tests -v
```

Аналогично для `model2` и `model3`.

## Особенности реализации

- Отображаемый результат моделей 2 и 3 ограничивается диапазоном 0–100%.
