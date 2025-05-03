# Installation de SilicaAnimus
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

# Utilisation et configuration des commandes de SilicaAnimus

## Configuration des commandes A FAIRE AVANT LE PREMIER LANCEMENT DU BOT

Les commandes sont par défaut utilisables par tout le monde et dans 
tous les salons. Il faut donc faire attention à bien régler le champ
d'utilisation de certaines commandes. Ces restrictions sont gérées par 
un administrateur du serveur discord

Aller dans les paramètres du serveur, puis `Integrations`, puis `Gerer` 
(sur la ligne de votre bot). A partir de ce panneau, on peut
régler des paramètres globaux d'utilisation du bot (utilisateurs et
salons). Une fois ceci fait, on peut accorder des dérogations d'utilisation
à certains utilisateurs ou groupes d'utilisateurs (roles) et également
des dérogations de salons

## Manuel d'utilisation des commandes

### Commande : `ping`
**Description :**  
Envoie un signal à l'application et affiche le temps de latence.

**Exemple :**  
```
/ping
```
*Réponse :*  
```
Pong Pong! Bot ping is 42 ms
```

---

### Commande : `echo`
**Description :**  
L'application répète le message envoyé par l'utilisateur.

**Arguments :**  
- **texte** : Texte à répéter.

**Exemple :**  
```
/echo texte="Bonjour tout le monde !"
```
*Réponse :*  
```
Bonjour tout le monde !
```

---

### Commande : `my_roles`
**Description :**  
Affiche la liste des rôles que l'utilisateur possède.

**Arguments :**  
- **montrer** *(optionnel)* : Indique si la réponse doit être visible publiquement (par défaut : privée).

**Exemple :**  
1. Réponse privée :  
```
/my_roles
```
*Réponse :*  
```
Tu possèdes les rôles suivants :
- @Admin
- @Membre
```

2. Réponse publique :  
```
/my_roles montrer=true
```
*Réponse :*  
```
Tu possèdes les rôles suivants :
- @Admin
- @Membre
```

---

### Commande : `whois`
**Description :**  
Affiche les utilisateurs ayant le rôle fourni en paramètre.

**Arguments :**  
- **rôle** : Rôle dont il faut lister les membres.
- **montrer** *(optionnel)* : Indique si la réponse doit être visible publiquement (par défaut : privée).

**Exemple :**  
```
/whois rôle=@Membre montrer=true
```
*Réponse :*  
```
Les membres ayant le rôle @Membre sont :
- @Utilisateur1
- @Utilisateur2
```

---

### Menu Contextuel : `Epingler`
**Description :**  
Permet d'épingler un message dans un salon.

**Exemple :**  
1. Faites un clic droit sur un message.  
2. Sélectionnez : `Application` puis `Epingler`.

*Réponse :*  
```
Message épinglé !
```

---

### Commande : `check_member`
**Description :**  
Vérifie si une personne est adhérente de l'association.

**Exemple :**  
```
/check_member
```
*Réponse :* Une fenêtre s'ouvre pour entrer le prénom et nom. Une fois soumis :  
```
Paul Bismuth est adhérent
```
ou  
```
Paul Bismuth n'est pas adhérent
```

---

### Commande : `give_role`
**Description :**  
Donne un rôle à tous les membres ayant un rôle spécifique.

**Arguments :**  
- **role_given** : Rôle à donner.  
- **user_group** : Groupe d'utilisateurs recevant le nouveau rôle.  
- **montrer** *(optionnel)* : Indique si la réponse doit être visible publiquement (par défaut : privée).

**Exemple :**  
```
/give_role role_given=@VIP user_group=@Membre
```
*Réponse :*  
```
Le rôle @VIP est accordé à :
- @Utilisateur1
- @Utilisateur2
```

---

### Commande : `make_membercheck`
**Description :**  
Ajoute le membre au groupe des adhérents sur le Discord.

**Exemple :**  
```
/make_membercheck
```
*Réponse :*  
Un bouton apparaît pour demander le rôle. En cliquant dessus, le bot vérifie l'adhésion et ajoute le rôle si applicable.

---

### Menu Contextuel : `Informations utilisateur`
**Description :**  
Affiche des informations sur un utilisateur.

**Exemple :**  
1. Faites un clic droit sur un utilisateur.  
2. Sélectionnez : `Application` pui `Informations utilisateur`.

*Réponse :*  
```
Informations sur l'utilisateur :
- Pseudo Discord : @Utilisateur
- Nom : Bismuth
- Prénom : Paul
```

---

### Commande : `update_member_list`
**Description :**  
Lance la procédure de mise à jour des adhérents sur le Discord.

**Exemple :**  
```
/update_member_list
```
*Réponse :*  
```
Ces utilisateurs gagneront le rôle membre :
- @Utilisateur1, @Utilisateur2

Ces utilisateurs conserveront leur rôle membre :
- @Utilisateur3, @Utilisateur4

Ces utilisateurs perdront leur rôle membre :
- @Utilisateur5
```
Des boutons pour confirmer ou annuler l'action sont également affichés.

---

*Cette documentation est conçue pour le bot Discord de La Voie du Thalos.*
```
