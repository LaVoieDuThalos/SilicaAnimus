# SilicaAnimus
Le bot du Discord de la Voie du Thalos

## Build docker image

Pour construire l'image Docker du Bot :

```bash
docker build -t silicaanimus:0.0.1 .
```

## Démarrage de l'image Docker

Pour démarrer l'image Docker du bot avec le fichier .env :

```bash
docker run -v ./src/SilicaAnimus/.env:/home/animus/code/SilicaAnimus/.env -it silicaanimus:0.0.1
```
