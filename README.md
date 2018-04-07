# scalable-chat
...
# How to run
0. git clone https://github.com/glkhvvldmr/scalable-chat && cd scalable-chat
1. Install requirements (requirements.txt) and Redis
1. Run redis 
2. Run server: python36 ./server.py --port=8888 --redis_host=localhost --redis_port=6379
3. Run client: python36 ./client.py -host localhost -port 8888
4. Start chat

Note: you can run many server instances and connect to them with client instances
