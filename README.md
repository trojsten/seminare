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
load dummy data
```sh
docker compose run --rm web python manage.py loaddata dummy-data.json
```
