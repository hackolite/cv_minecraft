# Fix: Camera Block Placement Client-Side

## Problème / Problem

**FR:** Quand je me mets côté client, je n'arrive pas à construire le bloc caméra (il ne peut pas être utilisé pour générer des screenshots).

**EN:** When on the client side, I cannot build the camera block (it cannot be used to generate screenshots).

## Cause Racine / Root Cause

Les blocs caméra placés par les joueurs ne recevaient pas de `block_id` automatique, contrairement aux caméras créées lors de l'initialisation du monde. Sans `block_id`, ces caméras ne pouvaient pas être interrogées via l'API WebSocket et donc ne pouvaient pas générer de screenshots.

Camera blocks placed by players were not receiving an automatic `block_id`, unlike cameras created during world initialization. Without a `block_id`, these cameras could not be queried via the WebSocket API and therefore could not generate screenshots.

## Solution

Modification du serveur pour auto-générer des `block_id` uniques pour tous les blocs caméra placés par les joueurs.

Modified the server to auto-generate unique `block_id`s for all camera blocks placed by players.

### Modifications / Changes

**Fichier / File:** `server.py`

1. **Ajout du compteur de caméras / Added camera counter:**
   ```python
   # In MinecraftServer.__init__
   self._camera_counter = 5  # Starts at 5 (0-4 used by initial cameras)
   ```

2. **Auto-génération du block_id / Auto-generation of block_id:**
   ```python
   # In _handle_block_place
   if block_type == BlockType.CAMERA:
       block_id = f"camera_{self._camera_counter}"
       self._camera_counter += 1
       self.logger.info(f"Auto-generated block_id '{block_id}' for camera block")
   ```

## Résultats / Results

### Avant / Before
- ❌ Caméras placées par les joueurs : pas de `block_id`
- ❌ Impossible de requêter via WebSocket
- ❌ Impossible de générer des screenshots

### Après / After
- ✅ Caméras placées par les joueurs : `block_id` auto-généré (camera_5, camera_6, etc.)
- ✅ Complètement interrogeable via l'API WebSocket
- ✅ Screenshots fonctionnent parfaitement

## Tests

Tous les tests passent avec succès / All tests pass successfully:

1. **Test de placement de base / Basic placement test**
   - Vérifie que les caméras reçoivent des block_id uniques
   - Vérifie que le compteur s'incrémente correctement
   - Vérifie que les blocs non-caméra ne reçoivent pas de block_id

2. **Test d'intégration / Integration test**
   - Place une caméra
   - La retrouve dans la liste des caméras
   - Requête sa vue via l'API WebSocket
   - Vérifie qu'elle peut générer des screenshots

3. **Test de destruction / Destruction test**
   - Place et détruit une caméra
   - Vérifie le nettoyage du block_id_map
   - Vérifie que les IDs ne sont jamais réutilisés

4. **Tests existants / Existing tests**
   - Tous les tests de métadonnées de blocs passent
   - Aucune régression détectée

## Utilisation / Usage

### Pour les Joueurs / For Players

1. Sélectionnez le bloc caméra dans votre inventaire (molette de la souris)
2. Placez-le avec clic droit (ou Ctrl+clic gauche)
3. Le serveur assignera automatiquement un `block_id` (camera_5, camera_6, etc.)
4. Vous pouvez maintenant utiliser cette caméra pour générer des screenshots!

### Pour Générer un Screenshot / To Generate a Screenshot

```bash
# Lister les caméras disponibles
python3 camera_view_query.py --list-cameras

# Générer un screenshot depuis votre caméra
python3 generate_camera_screenshot.py --camera-id camera_5

# Ou en deux étapes
python3 camera_view_query.py --camera-id camera_5 --output view.json
python3 camera_view_reconstruction.py --input view.json --output screenshot.png
```

## Compatibilité / Compatibility

- ✅ Compatible avec les caméras existantes (camera_0 à camera_4)
- ✅ Le compteur commence à 5 pour éviter les conflits
- ✅ Les IDs ne sont jamais réutilisés même après suppression
- ✅ Rétrocompatible avec le code client existant
