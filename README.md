# 🖋️ Filigranneur (Watermark Tool)

Script Python pour ajouter un filigrane **texte répété en diagonale** + **logo optionnel** sur :

- Images : JPG / JPEG / PNG  
- PDF (conversion en images puis reconstruction)

---

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

### 2. (Optionnel) Ajouter la police Bebas Neue

Télécharger la police **Bebas Neue** et placer le fichier `.ttf` dans le dossier du script :

```
BebasNeue-Regular.ttf
```

Ou préciser son chemin avec `--font-path`.

---

## ▶️ Utilisation

### ✅ Usage simple (dossier courant)

```bash
python3 filigranneur.py "Document non reproductible - 20260327" "logo.png"
```

- Traite tous les fichiers du dossier courant
- Génère des fichiers suffixés `_watermarked`

---

### 📁 Sur un dossier spécifique

```bash
python3 filigranneur.py "CONFIDENTIEL" "logo.png" --input ./mes_documents
```

---

### 🖋️ Avec Bebas Neue

```bash
python3 filigranneur.py "CONFIDENTIEL" "logo.png" \
  --font-path "./BebasNeue-Regular.ttf"
```

---

## ⚙️ Paramètres principaux

| Option | Description | Défaut |
|------|-------------|--------|
| `--opacity` | Opacité du texte (0–255) | 55 |
| `--logo-opacity` | Opacité du logo | 160 |
| `--font-size` | Taille du texte | auto |
| `--angle` | Angle du filigrane | 35° |
| `--spacing-x` | Espacement horizontal | auto |
| `--spacing-y` | Espacement vertical | auto |
| `--color` | Couleur texte (R,G,B) | 180,0,0 |
| `--logo-scale` | Taille du logo | 0.14 |
| `--dpi` | Qualité PDF | 160 |
| `--recursive` | Parcours sous-dossiers | off |

---

## 💡 Exemples

### 🔥 Filigrane visible

```bash
python3 filigranneur.py "DOCUMENT CONFIDENTIEL" "logo.png" \
  --opacity 75 \
  --font-size 72 \
  --spacing-x 380 \
  --spacing-y 170 \
  --dpi 180
```

---

### 👀 Filigrane discret

```bash
python3 filigranneur.py "INTERNE" \
  --opacity 40 \
  --font-size 56 \
  --spacing-x 460 \
  --spacing-y 220
```

### Exemple presque complet

```bash
python3 filigranneur.py "INTERNE - 20260327" \
  --input "input/" \
  --output-dir "output/" \
  --opacity 50 \
  --font-path "/Users/username/Library/Fonts/BebasNeue-Regular.ttf"
```

---

## 📌 Fonctionnement

### Images
- Ajoute un texte répété en diagonale
- Ajoute le logo dans les 4 coins

### PDF
- Conversion en image
- Application du filigrane
- Reconstruction en PDF

⚠️ **Important** :  
Le texte du PDF devient non sélectionnable (car rasterisé).

---

## 📂 Résultat

Fichier généré :

```
mon_fichier.pdf → mon_fichier_watermarked.pdf
image.jpg → image_watermarked.jpg
```

---

## 🧠 Bonnes pratiques

- Utiliser une opacité entre **50 et 80**
- Préférer une police lisible (Bebas Neue 👌)
- Ajuster `spacing` pour éviter surcharge ou vide

---

## 🛠️ Limitations

- PDF transformés en images (pas vectoriel)
- Pas de traitement parallèle (OK pour usage standard)

---

## ✅ TODO (si évolution future)

- Filigrane vectoriel pour PDF
- CLI plus avancée (mode fichier unique / batch)
- Parallélisation
- Configuration via fichier YAML

---

## ✨ Auteur

Script custom pour usage pro / perso 👍
