# Alias Support — frontend Angular

Interface Angular 22 de l'application de gestion des tickets. Elle consomme exclusivement l'API FastAPI sous `/api`.

## Prérequis

- Node.js 22.22.3 ou plus récent (Node 24 LTS convient)
- API FastAPI lancée sur `http://localhost:8000`

## Démarrage

```powershell
npm install
npm start
```

Le serveur Angular utilise `proxy.conf.json` pour transmettre `/api` au backend. Ouvrir ensuite `http://localhost:4200`.

## Vérification

```powershell
npm run build
npm test
```

La session est conservée dans le stockage local du navigateur. L'intercepteur HTTP joint le jeton JWT aux appels API et les gardes protègent les routes authentifiées et administrateur.
