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
docker run -it --env-file .env silicaanimus:0.0.1
```
