# seminare

## Compose magic
make migrations 
```shell
docker compose run --rm web python manage.py makemigrations
```
migrate 
```shell
docker compose run --rm web python manage.py migrate
```

generate dummy data 
```shell
docker compose run --rm web python manage.py generate_dummy_data
```
