"""Internacionalización / Multi-idioma para la aplicación."""

# ── Diccionario de traducciones ───────────────────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {
    'es': {
        'app.settings': 'Ajustes',
        'app.save': 'Guardar',
        'app.cancel': 'Cancelar',
        'app.close': 'Cerrar',
        'app.restart_required': 'Reinicia la aplicación para aplicar los cambios de idioma.',

        'settings.title': 'Ajustes de la aplicación',
        'settings.appearance': 'Apariencia',
        'settings.theme': 'Tema de color:',
        'settings.theme_dark': 'Oscuro (predeterminado)',
        'settings.theme_light': 'Claro',

        'settings.accessibility': 'Accesibilidad',
        'settings.font_size': 'Tamaño de fuente:',
        'settings.font_normal': 'Normal (predeterminado)',
        'settings.font_large': 'Grande (+25%)',

        'settings.language': 'Idioma',
        'settings.language_label': 'Idioma de la interfaz:',
        'settings.language_restart_note': 'El cambio de idioma se aplica al reiniciar la aplicación.',

        'settings.defaults': 'Valores por defecto',
        'settings.defaults_desc': 'Estos valores se aplicarán automáticamente cada vez que inicies un nuevo libro.',
        'settings.defaults_native': 'Campos WooCommerce nativos',
        'settings.defaults_custom': 'Campos personalizados del sitio',
        'settings.defaults_price': 'Precio (€):',
        'settings.defaults_stock': 'Stock inicial:',
        'settings.defaults_weight': 'Peso (kg):',
        'settings.defaults_length': 'Longitud (cm):',
        'settings.defaults_width': 'Anchura (cm):',
        'settings.defaults_height': 'Altura (cm):',
        'settings.defaults_status': 'Estado del producto:',
        'settings.defaults_status_draft': 'Borrador',
        'settings.defaults_status_publish': 'Publicado',
        'settings.defaults_catalog_visibility': 'Visibilidad en catálogo:',
        'settings.defaults_catalog_visible': 'Tienda y búsqueda',
        'settings.defaults_catalog_catalog': 'Solo tienda',
        'settings.defaults_catalog_search': 'Solo búsqueda',
        'settings.defaults_catalog_hidden': 'Oculto',
        'settings.defaults_tax_status': 'Estado fiscal:',
        'settings.defaults_tax_taxable': 'Sujeto a impuestos',
        'settings.defaults_tax_shipping': 'Solo envío',
        'settings.defaults_tax_none': 'Ninguno',
        'settings.defaults_load_custom': '🔄 Cargar campos del sitio activo',
        'settings.defaults_no_site': (
            'Conecta un sitio WooCommerce para poder cargar sus campos personalizados.\n'
            'Los campos nativos de WooCommerce (precio, stock, dimensiones…) '
            'están siempre disponibles.'
        ),
        'settings.defaults_custom_loaded': 'Campos personalizados cargados. Establece los valores por defecto:',
        'settings.defaults_custom_loading': 'Cargando campos del sitio...',
        'settings.defaults_custom_error': 'No se pudieron cargar los campos: {error}',

        'settings.saved_ok': 'Ajustes guardados correctamente.',
        'settings.save_error': 'Error al guardar los ajustes.',
    },

    'ca': {
        'app.settings': 'Ajustos',
        'app.save': 'Desar',
        'app.cancel': 'Cancel·lar',
        'app.close': 'Tancar',
        'app.restart_required': "Reinicia l'aplicació per aplicar els canvis d'idioma.",

        'settings.title': "Ajustos de l'aplicació",
        'settings.appearance': 'Aparença',
        'settings.theme': 'Tema de color:',
        'settings.theme_dark': 'Fosc (predeterminat)',
        'settings.theme_light': 'Clar',

        'settings.accessibility': 'Accessibilitat',
        'settings.font_size': 'Mida de lletra:',
        'settings.font_normal': 'Normal (predeterminat)',
        'settings.font_large': 'Gran (+25%)',

        'settings.language': 'Idioma',
        'settings.language_label': "Idioma de la interfície:",
        'settings.language_restart_note': "El canvi d'idioma s'aplica en reiniciar l'aplicació.",

        'settings.defaults': 'Valors per defecte',
        'settings.defaults_desc': 'Aquests valors s\'aplicaran automàticament cada vegada que iniciïs un llibre nou.',
        'settings.defaults_native': 'Camps WooCommerce natius',
        'settings.defaults_custom': 'Camps personalitzats del lloc',
        'settings.defaults_price': 'Preu (€):',
        'settings.defaults_stock': 'Estoc inicial:',
        'settings.defaults_weight': 'Pes (kg):',
        'settings.defaults_length': 'Longitud (cm):',
        'settings.defaults_width': 'Amplada (cm):',
        'settings.defaults_height': 'Alçada (cm):',
        'settings.defaults_status': 'Estat del producte:',
        'settings.defaults_status_draft': 'Esborrany',
        'settings.defaults_status_publish': 'Publicat',
        'settings.defaults_catalog_visibility': 'Visibilitat al catàleg:',
        'settings.defaults_catalog_visible': 'Botiga i cerca',
        'settings.defaults_catalog_catalog': 'Només botiga',
        'settings.defaults_catalog_search': 'Només cerca',
        'settings.defaults_catalog_hidden': 'Ocult',
        'settings.defaults_tax_status': 'Estat fiscal:',
        'settings.defaults_tax_taxable': 'Subjecte a impostos',
        'settings.defaults_tax_shipping': 'Només enviament',
        'settings.defaults_tax_none': 'Cap',
        'settings.defaults_load_custom': '🔄 Carregar camps del lloc actiu',
        'settings.defaults_no_site': (
            'Connecta un lloc WooCommerce per carregar els seus camps personalitzats.\n'
            'Els camps natius de WooCommerce (preu, estoc, dimensions…) '
            'sempre estan disponibles.'
        ),
        'settings.defaults_custom_loaded': 'Camps personalitzats carregats. Estableix els valors per defecte:',
        'settings.defaults_custom_loading': 'Carregant camps del lloc...',
        'settings.defaults_custom_error': 'No s\'han pogut carregar els camps: {error}',

        'settings.saved_ok': 'Ajustos desats correctament.',
        'settings.save_error': 'Error en desar els ajustos.',
    },

    'eu': {
        'app.settings': 'Ezarpenak',
        'app.save': 'Gorde',
        'app.cancel': 'Utzi',
        'app.close': 'Itxi',
        'app.restart_required': 'Hizkuntza aldaketak aplikatzeko, berrabiarazi aplikazioa.',

        'settings.title': 'Aplikazioaren ezarpenak',
        'settings.appearance': 'Itxura',
        'settings.theme': 'Kolore-gaia:',
        'settings.theme_dark': 'Iluna (lehenetsia)',
        'settings.theme_light': 'Argia',

        'settings.accessibility': 'Irisgarritasuna',
        'settings.font_size': 'Letra-tamaina:',
        'settings.font_normal': 'Normala (lehenetsia)',
        'settings.font_large': 'Handia (+%25)',

        'settings.language': 'Hizkuntza',
        'settings.language_label': 'Interfazeko hizkuntza:',
        'settings.language_restart_note': 'Hizkuntza aldaketa aplikatzeko berrabiarazi behar da.',

        'settings.defaults': 'Balio lehenetsiak',
        'settings.defaults_desc': 'Balio hauek automatikoki aplikatuko dira liburu berri bat hasten duzun bakoitzean.',
        'settings.defaults_native': 'WooCommerce eremu natiboak',
        'settings.defaults_custom': 'Guneko eremu pertsonalizatuak',
        'settings.defaults_price': 'Prezioa (€):',
        'settings.defaults_stock': 'Hasierako stocka:',
        'settings.defaults_weight': 'Pisua (kg):',
        'settings.defaults_length': 'Luzera (cm):',
        'settings.defaults_width': 'Zabalera (cm):',
        'settings.defaults_height': 'Altuera (cm):',
        'settings.defaults_status': 'Produktuaren egoera:',
        'settings.defaults_status_draft': 'Zirriborroa',
        'settings.defaults_status_publish': 'Argitaratua',
        'settings.defaults_catalog_visibility': 'Katalogoan ikusgarritasuna:',
        'settings.defaults_catalog_visible': 'Denda eta bilaketa',
        'settings.defaults_catalog_catalog': 'Denda soilik',
        'settings.defaults_catalog_search': 'Bilaketa soilik',
        'settings.defaults_catalog_hidden': 'Ezkutua',
        'settings.defaults_tax_status': 'Zerga egoera:',
        'settings.defaults_tax_taxable': 'Zergapekoa',
        'settings.defaults_tax_shipping': 'Bidalketa soilik',
        'settings.defaults_tax_none': 'Bat ere ez',
        'settings.defaults_load_custom': '🔄 Gune aktiboaren eremuak kargatu',
        'settings.defaults_no_site': (
            'Konektatu WooCommerce gune bat bere eremu pertsonalizatuak kargatzeko.\n'
            'WooCommerce eremu natiboak (prezioa, stocka, neurriak…) '
            'beti erabilgarri daude.'
        ),
        'settings.defaults_custom_loaded': 'Eremu pertsonalizatuak kargatuta. Ezarri balio lehenetsiak:',
        'settings.defaults_custom_loading': 'Gunearen eremuak kargatzen...',
        'settings.defaults_custom_error': 'Eremuak ezin izan dira kargatu: {error}',

        'settings.saved_ok': 'Ezarpenak ondo gorde dira.',
        'settings.save_error': 'Ezarpenak gordetzean errore bat gertatu da.',
    },

    'pt': {
        'app.settings': 'Definições',
        'app.save': 'Guardar',
        'app.cancel': 'Cancelar',
        'app.close': 'Fechar',
        'app.restart_required': 'Reinicia a aplicação para aplicar as alterações de idioma.',

        'settings.title': 'Definições da aplicação',
        'settings.appearance': 'Aparência',
        'settings.theme': 'Tema de cor:',
        'settings.theme_dark': 'Escuro (predefinido)',
        'settings.theme_light': 'Claro',

        'settings.accessibility': 'Acessibilidade',
        'settings.font_size': 'Tamanho da letra:',
        'settings.font_normal': 'Normal (predefinido)',
        'settings.font_large': 'Grande (+25%)',

        'settings.language': 'Idioma',
        'settings.language_label': 'Idioma da interface:',
        'settings.language_restart_note': 'A alteração do idioma é aplicada ao reiniciar a aplicação.',

        'settings.defaults': 'Valores predefinidos',
        'settings.defaults_desc': 'Estes valores serão aplicados automaticamente sempre que iniciar um novo livro.',
        'settings.defaults_native': 'Campos WooCommerce nativos',
        'settings.defaults_custom': 'Campos personalizados do site',
        'settings.defaults_price': 'Preço (€):',
        'settings.defaults_stock': 'Stock inicial:',
        'settings.defaults_weight': 'Peso (kg):',
        'settings.defaults_length': 'Comprimento (cm):',
        'settings.defaults_width': 'Largura (cm):',
        'settings.defaults_height': 'Altura (cm):',
        'settings.defaults_status': 'Estado do produto:',
        'settings.defaults_status_draft': 'Rascunho',
        'settings.defaults_status_publish': 'Publicado',
        'settings.defaults_catalog_visibility': 'Visibilidade no catálogo:',
        'settings.defaults_catalog_visible': 'Loja e pesquisa',
        'settings.defaults_catalog_catalog': 'Só loja',
        'settings.defaults_catalog_search': 'Só pesquisa',
        'settings.defaults_catalog_hidden': 'Oculto',
        'settings.defaults_tax_status': 'Estado fiscal:',
        'settings.defaults_tax_taxable': 'Sujeito a impostos',
        'settings.defaults_tax_shipping': 'Só envio',
        'settings.defaults_tax_none': 'Nenhum',
        'settings.defaults_load_custom': '🔄 Carregar campos do site ativo',
        'settings.defaults_no_site': (
            'Liga um site WooCommerce para carregar os seus campos personalizados.\n'
            'Os campos nativos do WooCommerce (preço, stock, dimensões…) '
            'estão sempre disponíveis.'
        ),
        'settings.defaults_custom_loaded': 'Campos personalizados carregados. Define os valores predefinidos:',
        'settings.defaults_custom_loading': 'A carregar campos do site...',
        'settings.defaults_custom_error': 'Não foi possível carregar os campos: {error}',

        'settings.saved_ok': 'Definições guardadas com sucesso.',
        'settings.save_error': 'Erro ao guardar as definições.',
    },

    'fr': {
        'app.settings': 'Paramètres',
        'app.save': 'Enregistrer',
        'app.cancel': 'Annuler',
        'app.close': 'Fermer',
        'app.restart_required': "Redémarrez l'application pour appliquer les changements de langue.",

        'settings.title': "Paramètres de l'application",
        'settings.appearance': 'Apparence',
        'settings.theme': 'Thème de couleur\u00a0:',
        'settings.theme_dark': 'Sombre (par défaut)',
        'settings.theme_light': 'Clair',

        'settings.accessibility': 'Accessibilité',
        'settings.font_size': 'Taille de police\u00a0:',
        'settings.font_normal': 'Normal (par défaut)',
        'settings.font_large': 'Grand (+25\u00a0%)',

        'settings.language': 'Langue',
        'settings.language_label': "Langue de l'interface\u00a0:",
        'settings.language_restart_note': "Le changement de langue s'applique au redémarrage de l'application.",

        'settings.defaults': 'Valeurs par défaut',
        'settings.defaults_desc': "Ces valeurs seront appliquées automatiquement à chaque nouveau livre.",
        'settings.defaults_native': 'Champs WooCommerce natifs',
        'settings.defaults_custom': 'Champs personnalisés du site',
        'settings.defaults_price': 'Prix (€)\u00a0:',
        'settings.defaults_stock': 'Stock initial\u00a0:',
        'settings.defaults_weight': 'Poids (kg)\u00a0:',
        'settings.defaults_length': 'Longueur (cm)\u00a0:',
        'settings.defaults_width': 'Largeur (cm)\u00a0:',
        'settings.defaults_height': 'Hauteur (cm)\u00a0:',
        'settings.defaults_status': 'Statut du produit\u00a0:',
        'settings.defaults_status_draft': 'Brouillon',
        'settings.defaults_status_publish': 'Publié',
        'settings.defaults_catalog_visibility': 'Visibilité dans le catalogue\u00a0:',
        'settings.defaults_catalog_visible': 'Boutique et recherche',
        'settings.defaults_catalog_catalog': 'Boutique uniquement',
        'settings.defaults_catalog_search': 'Recherche uniquement',
        'settings.defaults_catalog_hidden': 'Masqué',
        'settings.defaults_tax_status': 'Statut fiscal\u00a0:',
        'settings.defaults_tax_taxable': 'Imposable',
        'settings.defaults_tax_shipping': 'Livraison uniquement',
        'settings.defaults_tax_none': 'Aucun',
        'settings.defaults_load_custom': '🔄 Charger les champs du site actif',
        'settings.defaults_no_site': (
            'Connectez un site WooCommerce pour charger ses champs personnalisés.\n'
            'Les champs natifs WooCommerce (prix, stock, dimensions…) '
            'sont toujours disponibles.'
        ),
        'settings.defaults_custom_loaded': 'Champs personnalisés chargés. Définissez les valeurs par défaut\u00a0:',
        'settings.defaults_custom_loading': 'Chargement des champs du site...',
        'settings.defaults_custom_error': 'Impossible de charger les champs\u00a0: {error}',

        'settings.saved_ok': 'Paramètres enregistrés avec succès.',
        'settings.save_error': "Erreur lors de l'enregistrement des paramètres.",
    },

    'it': {
        'app.settings': 'Impostazioni',
        'app.save': 'Salva',
        'app.cancel': 'Annulla',
        'app.close': 'Chiudi',
        'app.restart_required': "Riavvia l'applicazione per applicare le modifiche alla lingua.",

        'settings.title': "Impostazioni dell'applicazione",
        'settings.appearance': 'Aspetto',
        'settings.theme': 'Tema colori:',
        'settings.theme_dark': 'Scuro (predefinito)',
        'settings.theme_light': 'Chiaro',

        'settings.accessibility': 'Accessibilità',
        'settings.font_size': 'Dimensione carattere:',
        'settings.font_normal': 'Normale (predefinito)',
        'settings.font_large': 'Grande (+25%)',

        'settings.language': 'Lingua',
        'settings.language_label': "Lingua dell'interfaccia:",
        'settings.language_restart_note': "Il cambio di lingua viene applicato al riavvio dell'applicazione.",

        'settings.defaults': 'Valori predefiniti',
        'settings.defaults_desc': 'Questi valori saranno applicati automaticamente ad ogni nuovo libro.',
        'settings.defaults_native': 'Campi WooCommerce nativi',
        'settings.defaults_custom': 'Campi personalizzati del sito',
        'settings.defaults_price': 'Prezzo (€):',
        'settings.defaults_stock': 'Stock iniziale:',
        'settings.defaults_weight': 'Peso (kg):',
        'settings.defaults_length': 'Lunghezza (cm):',
        'settings.defaults_width': 'Larghezza (cm):',
        'settings.defaults_height': 'Altezza (cm):',
        'settings.defaults_status': 'Stato del prodotto:',
        'settings.defaults_status_draft': 'Bozza',
        'settings.defaults_status_publish': 'Pubblicato',
        'settings.defaults_catalog_visibility': 'Visibilità nel catalogo:',
        'settings.defaults_catalog_visible': 'Negozio e ricerca',
        'settings.defaults_catalog_catalog': 'Solo negozio',
        'settings.defaults_catalog_search': 'Solo ricerca',
        'settings.defaults_catalog_hidden': 'Nascosto',
        'settings.defaults_tax_status': 'Stato fiscale:',
        'settings.defaults_tax_taxable': 'Imponibile',
        'settings.defaults_tax_shipping': 'Solo spedizione',
        'settings.defaults_tax_none': 'Nessuno',
        'settings.defaults_load_custom': '🔄 Carica campi del sito attivo',
        'settings.defaults_no_site': (
            'Connetti un sito WooCommerce per caricare i suoi campi personalizzati.\n'
            'I campi nativi WooCommerce (prezzo, stock, dimensioni…) '
            'sono sempre disponibili.'
        ),
        'settings.defaults_custom_loaded': 'Campi personalizzati caricati. Imposta i valori predefiniti:',
        'settings.defaults_custom_loading': 'Caricamento campi del sito...',
        'settings.defaults_custom_error': 'Impossibile caricare i campi: {error}',

        'settings.saved_ok': 'Impostazioni salvate correttamente.',
        'settings.save_error': 'Errore nel salvataggio delle impostazioni.',
    },

    'el': {
        'app.settings': 'Ρυθμίσεις',
        'app.save': 'Αποθήκευση',
        'app.cancel': 'Ακύρωση',
        'app.close': 'Κλείσιμο',
        'app.restart_required': 'Επανεκκινήστε την εφαρμογή για να εφαρμοστούν οι αλλαγές γλώσσας.',

        'settings.title': 'Ρυθμίσεις εφαρμογής',
        'settings.appearance': 'Εμφάνιση',
        'settings.theme': 'Χρωματικό θέμα:',
        'settings.theme_dark': 'Σκοτεινό (προεπιλογή)',
        'settings.theme_light': 'Φωτεινό',

        'settings.accessibility': 'Προσβασιμότητα',
        'settings.font_size': 'Μέγεθος γραμματοσειράς:',
        'settings.font_normal': 'Κανονικό (προεπιλογή)',
        'settings.font_large': 'Μεγάλο (+25%)',

        'settings.language': 'Γλώσσα',
        'settings.language_label': 'Γλώσσα διεπαφής:',
        'settings.language_restart_note': 'Η αλλαγή γλώσσας εφαρμόζεται κατά την επανεκκίνηση της εφαρμογής.',

        'settings.defaults': 'Προεπιλεγμένες τιμές',
        'settings.defaults_desc': 'Αυτές οι τιμές θα εφαρμόζονται αυτόματα σε κάθε νέο βιβλίο.',
        'settings.defaults_native': 'Εγγενή πεδία WooCommerce',
        'settings.defaults_custom': 'Προσαρμοσμένα πεδία ιστότοπου',
        'settings.defaults_price': 'Τιμή (€):',
        'settings.defaults_stock': 'Αρχικό απόθεμα:',
        'settings.defaults_weight': 'Βάρος (kg):',
        'settings.defaults_length': 'Μήκος (cm):',
        'settings.defaults_width': 'Πλάτος (cm):',
        'settings.defaults_height': 'Ύψος (cm):',
        'settings.defaults_status': 'Κατάσταση προϊόντος:',
        'settings.defaults_status_draft': 'Πρόχειρο',
        'settings.defaults_status_publish': 'Δημοσιευμένο',
        'settings.defaults_catalog_visibility': 'Ορατότητα καταλόγου:',
        'settings.defaults_catalog_visible': 'Κατάστημα και αναζήτηση',
        'settings.defaults_catalog_catalog': 'Μόνο κατάστημα',
        'settings.defaults_catalog_search': 'Μόνο αναζήτηση',
        'settings.defaults_catalog_hidden': 'Κρυφό',
        'settings.defaults_tax_status': 'Φορολογική κατάσταση:',
        'settings.defaults_tax_taxable': 'Φορολογητέο',
        'settings.defaults_tax_shipping': 'Μόνο αποστολή',
        'settings.defaults_tax_none': 'Κανένα',
        'settings.defaults_load_custom': '🔄 Φόρτωση πεδίων από τον ενεργό ιστότοπο',
        'settings.defaults_no_site': (
            'Συνδέστε έναν ιστότοπο WooCommerce για να φορτώσετε τα προσαρμοσμένα πεδία του.\n'
            'Τα εγγενή πεδία WooCommerce (τιμή, απόθεμα, διαστάσεις…) '
            'είναι πάντα διαθέσιμα.'
        ),
        'settings.defaults_custom_loaded': 'Τα πεδία φορτώθηκαν. Ορίστε τις προεπιλεγμένες τιμές:',
        'settings.defaults_custom_loading': 'Φόρτωση πεδίων ιστότοπου...',
        'settings.defaults_custom_error': 'Αδύνατη η φόρτωση πεδίων: {error}',

        'settings.saved_ok': 'Οι ρυθμίσεις αποθηκεύτηκαν επιτυχώς.',
        'settings.save_error': 'Σφάλμα κατά την αποθήκευση των ρυθμίσεων.',
    },

    'de': {
        'app.settings': 'Einstellungen',
        'app.save': 'Speichern',
        'app.cancel': 'Abbrechen',
        'app.close': 'Schließen',
        'app.restart_required': 'Starte die Anwendung neu, um die Sprachänderungen zu übernehmen.',

        'settings.title': 'Anwendungseinstellungen',
        'settings.appearance': 'Erscheinungsbild',
        'settings.theme': 'Farbthema:',
        'settings.theme_dark': 'Dunkel (Standard)',
        'settings.theme_light': 'Hell',

        'settings.accessibility': 'Barrierefreiheit',
        'settings.font_size': 'Schriftgröße:',
        'settings.font_normal': 'Normal (Standard)',
        'settings.font_large': 'Groß (+25%)',

        'settings.language': 'Sprache',
        'settings.language_label': 'Oberflächensprache:',
        'settings.language_restart_note': 'Die Sprachänderung wird nach einem Neustart der Anwendung übernommen.',

        'settings.defaults': 'Standardwerte',
        'settings.defaults_desc': 'Diese Werte werden automatisch bei jedem neuen Buch angewendet.',
        'settings.defaults_native': 'Native WooCommerce-Felder',
        'settings.defaults_custom': 'Benutzerdefinierte Felder der Website',
        'settings.defaults_price': 'Preis (€):',
        'settings.defaults_stock': 'Anfangsbestand:',
        'settings.defaults_weight': 'Gewicht (kg):',
        'settings.defaults_length': 'Länge (cm):',
        'settings.defaults_width': 'Breite (cm):',
        'settings.defaults_height': 'Höhe (cm):',
        'settings.defaults_status': 'Produktstatus:',
        'settings.defaults_status_draft': 'Entwurf',
        'settings.defaults_status_publish': 'Veröffentlicht',
        'settings.defaults_catalog_visibility': 'Katalogsichtbarkeit:',
        'settings.defaults_catalog_visible': 'Shop und Suche',
        'settings.defaults_catalog_catalog': 'Nur Shop',
        'settings.defaults_catalog_search': 'Nur Suche',
        'settings.defaults_catalog_hidden': 'Verborgen',
        'settings.defaults_tax_status': 'Steuerstatus:',
        'settings.defaults_tax_taxable': 'Steuerpflichtig',
        'settings.defaults_tax_shipping': 'Nur Versand',
        'settings.defaults_tax_none': 'Keiner',
        'settings.defaults_load_custom': '🔄 Felder der aktiven Website laden',
        'settings.defaults_no_site': (
            'Verbinde eine WooCommerce-Website, um ihre benutzerdefinierten Felder zu laden.\n'
            'Native WooCommerce-Felder (Preis, Bestand, Abmessungen…) '
            'sind immer verfügbar.'
        ),
        'settings.defaults_custom_loaded': 'Benutzerdefinierte Felder geladen. Lege die Standardwerte fest:',
        'settings.defaults_custom_loading': 'Felder der Website werden geladen...',
        'settings.defaults_custom_error': 'Felder konnten nicht geladen werden: {error}',

        'settings.saved_ok': 'Einstellungen erfolgreich gespeichert.',
        'settings.save_error': 'Fehler beim Speichern der Einstellungen.',
    },
}

# ── Estado global del idioma activo ──────────────────────────────────────────
_current_lang: str = 'es'


def set_language(lang_code: str) -> None:
    """Establece el idioma activo."""
    global _current_lang
    if lang_code in TRANSLATIONS:
        _current_lang = lang_code


def get_language() -> str:
    """Devuelve el código del idioma activo."""
    return _current_lang


def tr(key: str, fallback: str = '') -> str:
    """Devuelve la traducción para *key* en el idioma activo.
    
    Si no existe traducción en el idioma activo, cae al español.
    Si tampoco existe en español, devuelve *fallback* o la propia clave.
    """
    result = TRANSLATIONS.get(_current_lang, {}).get(key)
    if result is None:
        result = TRANSLATIONS['es'].get(key, fallback or key)
    return result


# ── Opciones de idioma disponibles ────────────────────────────────────────────
LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ('es', 'Español'),
    ('ca', 'Català'),
    ('eu', 'Euskara'),
    ('pt', 'Português'),
    ('fr', 'Français'),
    ('it', 'Italiano'),
    ('el', 'Ελληνικά'),
    ('de', 'Deutsch'),
]
