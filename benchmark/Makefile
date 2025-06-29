.PHONY: build run test clean

SERVICE_NAME = benchmark
PORT = 8001

build:
	docker build -t eberil/relink-$(SERVICE_NAME):latest .

run:
	docker-compose up -d

test:
	pytest tests/ -v

clean:
	docker-compose down
	docker rmi eberil/relink-$(SERVICE_NAME):latest || true
