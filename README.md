# scalable-chat
Чат-сервер на базе фрейморка tornado 5.0 Полностью асинхронный, Регистрировать юзеров и писать в БД не надо, достаточно того имени, которое при входе напишут. Но! Сервис должен запускаться в нескольких экземплярах на разных портах, адресах, машинах в  2, 3, 10 экземплярах. Но пользователи подключающиеся к этим разным экземплярам сервиса должны общаться в одном пространстве. Сам чат — простейшая реализация, но полностью асинхронная, python 3.6, с использованием async/await. Оформление как контейнеров докер и docker compose up - большой плюс, если нет инструкция как запускать.
# How to run
0. git clone https://github.com/glkhvvldmr/scalable-chat && cd scalable-chat
1. Install requirements (requirements.txt) and Redis
1. Run redis 
2. Run server: python36 ./server.py --port=8888 --redis_host=localhost --redis_port=6379
3. Run client: python36 ./client.py -host localhost -port 8888
4. Start chat

Note: you can run many server instances and connect to them with client instances