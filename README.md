# SilicaAnimus
Le bot du Discord de la Voie du Thalos

## Build docker image

Pour construire l'image Docker du Bot :

```bash
docker buildx build --platform linux/arm64/v8,linux/amd64 -t silicananimus:0.0.2 --load .
```

## Démarrage de l'image Docker

Pour démarrer l'image Docker du bot avec le fichier .env :

```bash
docker run -it --env-file .env silicaanimus:0.0.1
```
