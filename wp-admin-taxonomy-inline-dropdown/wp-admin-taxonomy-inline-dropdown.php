<?php
/**
 * Plugin Name: Admin Power Tools
 * Description: Power-ups para admin listados: taxonomy inline dropdown, producto destacado asincrono y excerpt inline editable.
 * Version: 1.1.0
 * Author: Book Uploader
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

if ( ! class_exists( 'Admin_Power_Tools' ) ) {
    class Admin_Power_Tools {
        const OPTION_TAX_MAP = 'apt_post_type_taxonomy_map';
        const OPTION_FEATURED_ENABLED = 'apt_async_featured_enabled';
        const OPTION_EXCERPT_MAP = 'apt_excerpt_post_type_map';
        const OPTION_SELECT_FIELD_MAP = 'apt_select_field_post_type_map';

        const NONCE_ACTION_SAVE_TERM = 'apt_save_inline_term';
        const NONCE_ACTION_FETCH_TERM = 'apt_fetch_inline_terms';
        const NONCE_ACTION_FETCH_SELECT_FIELD = 'apt_fetch_select_field_values';
        const NONCE_ACTION_SAVE_SELECT_FIELD = 'apt_save_select_field_value';
        const NONCE_ACTION_SAVE_FEATURED = 'apt_save_featured';
        const NONCE_ACTION_SAVE_EXCERPT = 'apt_save_excerpt';

        const COLUMN_FEATURED = 'apt_featured_toggle';
        const COLUMN_EXCERPT = 'apt_excerpt_inline';
        const COLUMN_SELECT_FIELD = 'apt_select_field_inline';

        public function __construct() {
            add_action( 'admin_menu', array( $this, 'register_settings_page' ) );
            add_action( 'admin_init', array( $this, 'register_settings' ) );

            add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_admin_assets' ) );

            add_action( 'current_screen', array( $this, 'register_list_hooks_for_screen' ) );

            add_action( 'wp_ajax_apt_get_current_terms', array( $this, 'ajax_get_current_terms' ) );
            add_action( 'wp_ajax_apt_set_term', array( $this, 'ajax_set_term' ) );
            add_action( 'wp_ajax_apt_get_current_select_field', array( $this, 'ajax_get_current_select_field' ) );
            add_action( 'wp_ajax_apt_set_select_field', array( $this, 'ajax_set_select_field' ) );
            add_action( 'wp_ajax_apt_set_featured', array( $this, 'ajax_set_featured' ) );
            add_action( 'wp_ajax_apt_set_excerpt', array( $this, 'ajax_set_excerpt' ) );
        }

        public function register_settings_page() {
            add_options_page(
                'Taxonomy Inline Dropdown',
                'Admin Power Tools',
                'manage_options',
                'apt-settings',
                array( $this, 'render_settings_page' )
            );
        }

        public function register_settings() {
            register_setting(
                'apt_settings_group',
                self::OPTION_TAX_MAP,
                array( $this, 'sanitize_tax_map_settings' )
            );

            register_setting(
                'apt_settings_group',
                self::OPTION_FEATURED_ENABLED,
                array( $this, 'sanitize_featured_setting' )
            );

            register_setting(
                'apt_settings_group',
                self::OPTION_EXCERPT_MAP,
                array( $this, 'sanitize_excerpt_map_settings' )
            );

            register_setting(
                'apt_settings_group',
                self::OPTION_SELECT_FIELD_MAP,
                array( $this, 'sanitize_select_field_map_settings' )
            );

            add_settings_section(
                'apt_main_section',
                'Configuracion de power tools',
                function() {
                    echo '<p>Configura las mejoras de productividad en listados de admin para trabajar contenido a gran escala.</p>';
                },
                'apt-settings'
            );

            add_settings_field(
                'apt_tax_mapping_field',
                'Asignacion por tipo de post',
                array( $this, 'render_mapping_field' ),
                'apt-settings',
                'apt_main_section'
            );

            add_settings_field(
                'apt_featured_field',
                'Productos destacados asincronos',
                array( $this, 'render_featured_field' ),
                'apt-settings',
                'apt_main_section'
            );

            add_settings_field(
                'apt_excerpt_field',
                'Columna excerpt inline',
                array( $this, 'render_excerpt_field' ),
                'apt-settings',
                'apt_main_section'
            );

            add_settings_field(
                'apt_select_field_inline',
                'Columna inline para campos de seleccion (ACF/Meta)',
                array( $this, 'render_select_field_mapping' ),
                'apt-settings',
                'apt_main_section'
            );
        }

        public function sanitize_tax_map_settings( $input ) {
            $clean = array();
            $input = is_array( $input ) ? $input : array();

            $post_types = get_post_types( array( 'show_ui' => true ), 'names' );

            foreach ( $input as $post_type => $taxonomy ) {
                $post_type = sanitize_key( $post_type );
                $taxonomy = sanitize_key( $taxonomy );

                if ( ! in_array( $post_type, $post_types, true ) ) {
                    continue;
                }

                if ( empty( $taxonomy ) ) {
                    continue;
                }

                $tax_obj = get_taxonomy( $taxonomy );
                if ( ! $tax_obj ) {
                    continue;
                }

                if ( empty( $tax_obj->show_admin_column ) ) {
                    continue;
                }

                if ( ! is_object_in_taxonomy( $post_type, $taxonomy ) ) {
                    continue;
                }

                $clean[ $post_type ] = $taxonomy;
            }

            return $clean;
        }

        public function sanitize_featured_setting( $input ) {
            return empty( $input ) ? 0 : 1;
        }

        public function sanitize_excerpt_map_settings( $input ) {
            $clean = array();
            $input = is_array( $input ) ? $input : array();
            $post_types = get_post_types( array( 'show_ui' => true ), 'names' );

            foreach ( $input as $post_type => $value ) {
                $post_type = sanitize_key( $post_type );
                if ( in_array( $post_type, $post_types, true ) && ! empty( $value ) ) {
                    $clean[ $post_type ] = 1;
                }
            }

            return $clean;
        }

        public function sanitize_select_field_map_settings( $input ) {
            $clean = array();
            $input = is_array( $input ) ? $input : array();
            $post_types = get_post_types( array( 'show_ui' => true ), 'names' );

            foreach ( $input as $post_type => $field_id ) {
                $post_type = sanitize_key( $post_type );
                $field_id = sanitize_text_field( wp_unslash( $field_id ) );

                if ( ! in_array( $post_type, $post_types, true ) || empty( $field_id ) ) {
                    continue;
                }

                $candidates = $this->get_select_field_candidates_for_post_type( $post_type );
                if ( isset( $candidates[ $field_id ] ) ) {
                    $clean[ $post_type ] = $field_id;
                }
            }

            return $clean;
        }

        private function normalize_choice_options( $choices ) {
            $normalized = array();

            if ( ! is_array( $choices ) ) {
                return $normalized;
            }

            foreach ( $choices as $value => $label ) {
                $value = (string) $value;
                $label = is_scalar( $label ) ? (string) $label : $value;
                if ( '' === $value ) {
                    continue;
                }
                $normalized[] = array(
                    'value' => $value,
                    'label' => $label,
                );
            }

            return $normalized;
        }

        private function get_select_field_candidates_for_post_type( $post_type ) {
            $candidates = array();

            if ( function_exists( 'acf_get_field_groups' ) && function_exists( 'acf_get_fields' ) ) {
                $field_groups = acf_get_field_groups( array( 'post_type' => $post_type ) );

                if ( is_array( $field_groups ) ) {
                    foreach ( $field_groups as $field_group ) {
                        $fields = acf_get_fields( $field_group );
                        if ( ! is_array( $fields ) ) {
                            continue;
                        }

                        foreach ( $fields as $field ) {
                            $type = isset( $field['type'] ) ? (string) $field['type'] : '';
                            if ( ! in_array( $type, array( 'select', 'radio', 'checkbox' ), true ) ) {
                                continue;
                            }

                            $choices = isset( $field['choices'] ) ? $this->normalize_choice_options( $field['choices'] ) : array();
                            if ( empty( $choices ) ) {
                                continue;
                            }

                            $field_key = isset( $field['key'] ) ? (string) $field['key'] : '';
                            $field_name = isset( $field['name'] ) ? (string) $field['name'] : '';
                            if ( '' === $field_key || '' === $field_name ) {
                                continue;
                            }

                            $field_id = 'acf:' . $field_key;
                            $label = ! empty( $field['label'] ) ? (string) $field['label'] : $field_name;
                            $group_title = ! empty( $field_group['title'] ) ? (string) $field_group['title'] : 'ACF';
                            $multiple = ( 'checkbox' === $type ) || ( 'select' === $type && ! empty( $field['multiple'] ) );

                            $candidates[ $field_id ] = array(
                                'id' => $field_id,
                                'source' => 'acf',
                                'label' => $label . ' (' . $field_name . ') - ' . $group_title,
                                'field_key' => $field_key,
                                'field_name' => $field_name,
                                'meta_key' => $field_name,
                                'multiple' => $multiple,
                                'choices' => $choices,
                            );
                        }
                    }
                }
            }

            if ( function_exists( 'get_registered_meta_keys' ) ) {
                $registered = get_registered_meta_keys( 'post', $post_type );
                if ( is_array( $registered ) ) {
                    foreach ( $registered as $meta_key => $meta_args ) {
                        $schema = array();
                        if ( ! empty( $meta_args['show_in_rest'] ) && is_array( $meta_args['show_in_rest'] ) && ! empty( $meta_args['show_in_rest']['schema'] ) && is_array( $meta_args['show_in_rest']['schema'] ) ) {
                            $schema = $meta_args['show_in_rest']['schema'];
                        }

                        $enum = array();
                        $multiple = false;
                        if ( ! empty( $schema['enum'] ) && is_array( $schema['enum'] ) ) {
                            $enum = $schema['enum'];
                        } elseif ( ! empty( $schema['type'] ) && 'array' === $schema['type'] && ! empty( $schema['items'] ) && is_array( $schema['items'] ) && ! empty( $schema['items']['enum'] ) && is_array( $schema['items']['enum'] ) ) {
                            $enum = $schema['items']['enum'];
                            $multiple = true;
                        }

                        if ( empty( $enum ) ) {
                            continue;
                        }

                        $choices = array();
                        foreach ( $enum as $enum_value ) {
                            if ( ! is_scalar( $enum_value ) ) {
                                continue;
                            }
                            $enum_value = (string) $enum_value;
                            if ( '' === $enum_value ) {
                                continue;
                            }
                            $choices[] = array(
                                'value' => $enum_value,
                                'label' => $enum_value,
                            );
                        }

                        if ( empty( $choices ) ) {
                            continue;
                        }

                        $field_id = 'meta:' . $meta_key;
                        if ( isset( $candidates[ $field_id ] ) ) {
                            continue;
                        }

                        $candidates[ $field_id ] = array(
                            'id' => $field_id,
                            'source' => 'meta',
                            'label' => $meta_key . ' (Meta registrado)',
                            'field_key' => '',
                            'field_name' => $meta_key,
                            'meta_key' => $meta_key,
                            'multiple' => $multiple,
                            'choices' => $choices,
                        );
                    }
                }
            }

            $extra_candidates = apply_filters( 'apt_inline_select_field_candidates', array(), $post_type );
            if ( is_array( $extra_candidates ) ) {
                foreach ( $extra_candidates as $extra ) {
                    if ( ! is_array( $extra ) ) {
                        continue;
                    }

                    $field_id = ! empty( $extra['id'] ) ? (string) $extra['id'] : '';
                    $label = ! empty( $extra['label'] ) ? (string) $extra['label'] : '';
                    $meta_key = ! empty( $extra['meta_key'] ) ? (string) $extra['meta_key'] : '';
                    $choices = ! empty( $extra['choices'] ) ? $this->normalize_choice_options( $extra['choices'] ) : array();
                    $multiple = ! empty( $extra['multiple'] );

                    if ( '' === $field_id || '' === $label || '' === $meta_key || empty( $choices ) ) {
                        continue;
                    }

                    if ( isset( $candidates[ $field_id ] ) ) {
                        continue;
                    }

                    $candidates[ $field_id ] = array(
                        'id' => $field_id,
                        'source' => 'meta',
                        'label' => $label,
                        'field_key' => '',
                        'field_name' => $meta_key,
                        'meta_key' => $meta_key,
                        'multiple' => $multiple,
                        'choices' => $choices,
                    );
                }
            }

            uasort(
                $candidates,
                function( $a, $b ) {
                    return strcasecmp( $a['label'], $b['label'] );
                }
            );

            return $candidates;
        }

        private function get_select_field_values_for_post( $post_id, $field_config ) {
            $values = array();

            if ( ! empty( $field_config['source'] ) && 'acf' === $field_config['source'] && function_exists( 'get_field' ) ) {
                $raw = get_field( $field_config['field_name'], $post_id, false );
            } else {
                $raw = get_post_meta( $post_id, $field_config['meta_key'], true );
            }

            if ( is_array( $raw ) ) {
                foreach ( $raw as $item ) {
                    if ( is_scalar( $item ) ) {
                        $value = (string) $item;
                        if ( '' !== $value ) {
                            $values[] = $value;
                        }
                    }
                }
            } elseif ( is_scalar( $raw ) ) {
                $value = (string) $raw;
                if ( '' !== $value ) {
                    $values[] = $value;
                }
            }

            return array_values( array_unique( $values ) );
        }

        private function save_select_field_values_for_post( $post_id, $field_config, $values ) {
            $values = is_array( $values ) ? $values : array();
            $values = array_values( array_unique( $values ) );

            $save_value = ! empty( $field_config['multiple'] )
                ? $values
                : ( ! empty( $values[0] ) ? $values[0] : '' );

            if ( ! empty( $field_config['source'] ) && 'acf' === $field_config['source'] && function_exists( 'update_field' ) ) {
                $acf_selector = ! empty( $field_config['field_key'] ) ? $field_config['field_key'] : $field_config['field_name'];
                update_field( $acf_selector, $save_value, $post_id );
                return true;
            }

            if ( '' === $save_value || array() === $save_value ) {
                delete_post_meta( $post_id, $field_config['meta_key'] );
                return true;
            }

            update_post_meta( $post_id, $field_config['meta_key'], $save_value );
            return true;
        }

        public function render_mapping_field() {
            $saved = $this->get_mapping();
            $post_types = get_post_types( array( 'show_ui' => true ), 'objects' );

            echo '<table class="widefat striped" style="max-width: 900px">';
            echo '<thead><tr><th>Tipo de post</th><th>Taxonomia editable en columna</th><th>Estado</th></tr></thead><tbody>';

            foreach ( $post_types as $post_type ) {
                $taxonomies = get_object_taxonomies( $post_type->name, 'objects' );
                $eligible = array();

                foreach ( $taxonomies as $tax_obj ) {
                    if ( ! empty( $tax_obj->show_ui ) && ! empty( $tax_obj->show_admin_column ) ) {
                        $eligible[] = $tax_obj;
                    }
                }

                $selected = isset( $saved[ $post_type->name ] ) ? $saved[ $post_type->name ] : '';

                echo '<tr>';
                echo '<td><strong>' . esc_html( $post_type->labels->singular_name ) . '</strong><br><code>' . esc_html( $post_type->name ) . '</code></td>';
                echo '<td>';
                echo '<select name="' . esc_attr( self::OPTION_TAX_MAP ) . '[' . esc_attr( $post_type->name ) . ']" style="min-width: 260px">';
                echo '<option value="">Desactivado</option>';

                foreach ( $eligible as $tax_obj ) {
                    echo '<option value="' . esc_attr( $tax_obj->name ) . '" ' . selected( $selected, $tax_obj->name, false ) . '>';
                    echo esc_html( $tax_obj->labels->singular_name . ' (' . $tax_obj->name . ')' );
                    echo '</option>';
                }

                echo '</select>';
                echo '</td>';

                if ( empty( $eligible ) ) {
                    echo '<td><span style="color:#b32d2e">Sin taxonomias elegibles (activa show_admin_column en la taxonomia)</span></td>';
                } else {
                    echo '<td><span style="color:#2271b1">OK</span></td>';
                }

                echo '</tr>';
            }

            echo '</tbody></table>';
        }

        public function render_featured_field() {
            $enabled = (int) get_option( self::OPTION_FEATURED_ENABLED, 0 );
            echo '<label>';
            echo '<input type="checkbox" name="' . esc_attr( self::OPTION_FEATURED_ENABLED ) . '" value="1" ' . checked( 1, $enabled, false ) . ' /> ';
            echo 'Activar toggle asincrono para "producto destacado" en listados de productos';
            echo '</label>';
        }

        public function render_excerpt_field() {
            $saved = $this->get_excerpt_map();
            $post_types = get_post_types( array( 'show_ui' => true ), 'objects' );

            echo '<table class="widefat striped" style="max-width: 900px">';
            echo '<thead><tr><th>Tipo de post</th><th>Activar columna excerpt inline</th></tr></thead><tbody>';

            foreach ( $post_types as $post_type ) {
                $checked = ! empty( $saved[ $post_type->name ] );
                echo '<tr>';
                echo '<td><strong>' . esc_html( $post_type->labels->singular_name ) . '</strong><br><code>' . esc_html( $post_type->name ) . '</code></td>';
                echo '<td><label><input type="checkbox" name="' . esc_attr( self::OPTION_EXCERPT_MAP ) . '[' . esc_attr( $post_type->name ) . ']" value="1" ' . checked( true, $checked, false ) . ' /> Activar</label></td>';
                echo '</tr>';
            }

            echo '</tbody></table>';
        }

        public function render_select_field_mapping() {
            $saved = $this->get_select_field_map();
            $post_types = get_post_types( array( 'show_ui' => true ), 'objects' );

            echo '<table class="widefat striped" style="max-width: 900px">';
            echo '<thead><tr><th>Tipo de post</th><th>Campo de seleccion inline</th><th>Estado</th></tr></thead><tbody>';

            foreach ( $post_types as $post_type ) {
                $candidates = $this->get_select_field_candidates_for_post_type( $post_type->name );
                $selected = isset( $saved[ $post_type->name ] ) ? $saved[ $post_type->name ] : '';

                echo '<tr>';
                echo '<td><strong>' . esc_html( $post_type->labels->singular_name ) . '</strong><br><code>' . esc_html( $post_type->name ) . '</code></td>';
                echo '<td>';
                echo '<select name="' . esc_attr( self::OPTION_SELECT_FIELD_MAP ) . '[' . esc_attr( $post_type->name ) . ']" style="min-width: 360px">';
                echo '<option value="">Desactivado</option>';

                foreach ( $candidates as $candidate ) {
                    $meta = ! empty( $candidate['multiple'] ) ? 'multiple' : 'simple';
                    $label = $candidate['label'] . ' [' . $meta . ']';
                    echo '<option value="' . esc_attr( $candidate['id'] ) . '" ' . selected( $selected, $candidate['id'], false ) . '>';
                    echo esc_html( $label );
                    echo '</option>';
                }

                echo '</select>';
                echo '</td>';

                if ( empty( $candidates ) ) {
                    echo '<td><span style="color:#b32d2e">Sin campos de seleccion elegibles (ACF select/radio/checkbox o meta registrado con enum)</span></td>';
                } else {
                    echo '<td><span style="color:#2271b1">OK</span></td>';
                }

                echo '</tr>';
            }

            echo '</tbody></table>';
        }

        public function render_settings_page() {
            if ( ! current_user_can( 'manage_options' ) ) {
                return;
            }

            echo '<div class="wrap">';
            echo '<h1>Admin Power Tools</h1>';
            echo '<form method="post" action="options.php">';
            settings_fields( 'apt_settings_group' );
            do_settings_sections( 'apt-settings' );
            submit_button( 'Guardar configuracion' );
            echo '</form>';
            echo '</div>';
        }

        public function register_list_hooks_for_screen( $screen ) {
            if ( ! $screen || 'edit' !== $screen->base || empty( $screen->post_type ) ) {
                return;
            }

            $post_type = $screen->post_type;

            add_filter( "manage_{$post_type}_posts_columns", array( $this, 'filter_admin_columns' ), 20 );
            add_action( "manage_{$post_type}_posts_custom_column", array( $this, 'render_custom_column' ), 10, 2 );
        }

        public function filter_admin_columns( $columns ) {
            $screen = get_current_screen();
            if ( ! $screen || empty( $screen->post_type ) ) {
                return $columns;
            }

            $post_type = $screen->post_type;

            if ( $this->is_excerpt_enabled_for_post_type( $post_type ) ) {
                $columns[ self::COLUMN_EXCERPT ] = 'Descripcion corta';
            }

            if ( $this->get_active_select_field_config_for_post_type( $post_type ) ) {
                $columns[ self::COLUMN_SELECT_FIELD ] = 'Campo seleccion';
            }

            if ( 'product' === $post_type && $this->is_featured_async_enabled() ) {
                if ( isset( $columns['featured'] ) ) {
                    unset( $columns['featured'] );
                }
                if ( isset( $columns['is_featured'] ) ) {
                    unset( $columns['is_featured'] );
                }
                $columns[ self::COLUMN_FEATURED ] = 'Destacado';
            }

            return $columns;
        }

        public function render_custom_column( $column, $post_id ) {
            if ( self::COLUMN_EXCERPT === $column ) {
                $excerpt = get_post_field( 'post_excerpt', $post_id );
                $preview = $excerpt ? wp_trim_words( $excerpt, 14, '...' ) : '';

                echo '<div class="apt-excerpt-inline-wrap" data-post-id="' . esc_attr( $post_id ) . '">';
                echo '<input type="text" class="apt-excerpt-preview" readonly value="' . esc_attr( $preview ) . '" placeholder="Sin descripcion corta" />';
                echo '<button type="button" class="button button-small apt-excerpt-edit-btn" data-full="' . esc_attr( $excerpt ) . '">Editar</button>';
                echo '</div>';
                return;
            }

            if ( self::COLUMN_SELECT_FIELD === $column ) {
                echo '<span class="apt-select-inline-placeholder">Cargando...</span>';
                return;
            }

            if ( self::COLUMN_FEATURED === $column ) {
                $checked = false;
                if ( function_exists( 'wc_get_product' ) ) {
                    $product = wc_get_product( $post_id );
                    if ( $product ) {
                        $checked = $product->is_featured();
                    }
                } else {
                    $featured = get_post_meta( $post_id, '_featured', true );
                    $checked = ( 'yes' === $featured );
                }
                echo '<label class="apt-featured-switch">';
                echo '<input type="checkbox" class="apt-featured-toggle" data-post-id="' . esc_attr( $post_id ) . '" ' . checked( true, $checked, false ) . ' />';
                echo '<span class="apt-featured-slider"></span>';
                echo '</label>';
            }
        }

        public function enqueue_admin_assets( $hook_suffix ) {
            if ( 'edit.php' !== $hook_suffix ) {
                return;
            }

            $screen = get_current_screen();
            if ( ! $screen || empty( $screen->post_type ) ) {
                return;
            }

            if ( ! current_user_can( 'edit_posts' ) ) {
                return;
            }

            $post_type = $screen->post_type;
            $mapping = $this->get_mapping();
            $taxonomy_enabled = ! empty( $mapping[ $post_type ] );
            $excerpt_enabled = $this->is_excerpt_enabled_for_post_type( $post_type );
            $featured_enabled = ( 'product' === $post_type && $this->is_featured_async_enabled() );
            $select_field_config = $this->get_active_select_field_config_for_post_type( $post_type );
            $select_field_enabled = ! empty( $select_field_config );

            if ( ! $taxonomy_enabled && ! $excerpt_enabled && ! $featured_enabled && ! $select_field_enabled ) {
                return;
            }

            $handle = 'apt-admin-list-tools';
            wp_register_script( $handle, '', array( 'jquery' ), '1.1.0', true );
            wp_enqueue_script( $handle );

            $data = array(
                'ajaxUrl' => admin_url( 'admin-ajax.php' ),
                'postType' => $post_type,
                'taxonomyEnabled' => false,
                'excerptEnabled' => $excerpt_enabled,
                'featuredEnabled' => $featured_enabled,
                'selectFieldEnabled' => $select_field_enabled,
                'taxonomy' => '',
                'columnClass' => '',
                'terms' => array(),
                'placeholder' => '',
                'selectFieldId' => '',
                'selectFieldColumnClass' => '',
                'selectFieldChoices' => array(),
                'selectFieldPlaceholder' => '',
                'selectFieldMultiple' => true,
                'fetchNonce' => wp_create_nonce( self::NONCE_ACTION_FETCH_TERM ),
                'saveTermNonce' => wp_create_nonce( self::NONCE_ACTION_SAVE_TERM ),
                'fetchSelectFieldNonce' => wp_create_nonce( self::NONCE_ACTION_FETCH_SELECT_FIELD ),
                'saveSelectFieldNonce' => wp_create_nonce( self::NONCE_ACTION_SAVE_SELECT_FIELD ),
                'saveFeaturedNonce' => wp_create_nonce( self::NONCE_ACTION_SAVE_FEATURED ),
                'saveExcerptNonce' => wp_create_nonce( self::NONCE_ACTION_SAVE_EXCERPT ),
            );

            if ( $taxonomy_enabled ) {
                $taxonomy = $mapping[ $post_type ];
                $tax_obj = get_taxonomy( $taxonomy );
                if ( $tax_obj && ! empty( $tax_obj->show_admin_column ) ) {
                    $terms = get_terms(
                        array(
                            'taxonomy' => $taxonomy,
                            'hide_empty' => false,
                        )
                    );

                    if ( ! is_wp_error( $terms ) ) {
                        $terms_payload = array();
                        foreach ( $terms as $term ) {
                            $terms_payload[] = array(
                                'id' => (int) $term->term_id,
                                'name' => $term->name,
                            );
                        }

                        $column_key = 'taxonomy-' . $taxonomy;
                        $placeholder = 'Seleccionar ' . ( ! empty( $tax_obj->labels->singular_name ) ? $tax_obj->labels->singular_name : $taxonomy );

                        $data['taxonomyEnabled'] = true;
                        $data['taxonomy'] = $taxonomy;
                        $data['columnClass'] = 'column-' . $column_key;
                        $data['terms'] = $terms_payload;
                        $data['placeholder'] = $placeholder;
                    }
                }
            }

            if ( $select_field_enabled ) {
                $choices_payload = array();
                foreach ( $select_field_config['choices'] as $choice ) {
                    $choices_payload[] = array(
                        'id' => (string) $choice['value'],
                        'name' => (string) $choice['label'],
                    );
                }

                $data['selectFieldId'] = $select_field_config['id'];
                $data['selectFieldColumnClass'] = 'column-' . self::COLUMN_SELECT_FIELD;
                $data['selectFieldChoices'] = $choices_payload;
                $data['selectFieldPlaceholder'] = 'Seleccionar';
                $data['selectFieldMultiple'] = ! empty( $select_field_config['multiple'] );
            }

            wp_add_inline_script( $handle, 'window.APT = ' . wp_json_encode( $data ) . ';', 'before' );

            $script = <<<'JS'
(function($){
    function toast(message) {
        if (window.wp && wp.a11y && wp.a11y.speak) {
            wp.a11y.speak(message);
        }
    }

    function showInlineStatus($origin, type, message) {
        var $cell = $origin.closest('td');
        if (!$cell.length) {
            return;
        }

        var $badge = $cell.find('.apt-inline-status').first();
        if (!$badge.length) {
            $badge = $('<span class="apt-inline-status"></span>');
            $cell.append($badge);
        }

        $badge.removeClass('is-success is-error is-pending').addClass('is-' + type).text(message).stop(true, true).show();
        window.setTimeout(function(){
            $badge.fadeOut(300);
        }, 2200);
    }

    function getPostIds() {
        var ids = [];
        $('#the-list tr[id^="post-"]').each(function(){
            var rowId = $(this).attr('id') || '';
            var postId = parseInt(rowId.replace('post-', ''), 10);
            if (!isNaN(postId) && postId > 0) {
                ids.push(postId);
            }
        });
        return ids;
    }

    function buildSelect(options, currentValue, multiple, placeholder) {
        var selectedMap = {};
        var currentIds = Array.isArray(currentValue) ? currentValue : (currentValue ? [currentValue] : []);

        currentIds.forEach(function(termId){
            selectedMap[String(termId)] = true;
        });

        var attrs = multiple ? ' multiple' : '';
        var select = $('<select class="apt-inline-term-select"' + attrs + ' style="width:160px;max-width:100%;font-size:10px;min-height:130px;padding:0;appearance:none;border-radius:3px"></select>');

        if (!multiple && placeholder) {
            select.append($('<option></option>').val('').text(placeholder));
        }

        (options || []).forEach(function(term){
            var opt = $('<option></option>').val(String(term.id)).text(term.name);
            if (selectedMap[String(term.id)]) {
                opt.prop('selected', true);
            }
            select.append(opt);
        });

        return select;
    }

    function updateSelectEmptyState($select) {
        var value = $select.val();
        var hasSelection = false;

        if (Array.isArray(value)) {
            hasSelection = value.length > 0;
        } else {
            hasSelection = !!value;
        }

        $select.toggleClass('is-empty', !hasSelection);
    }

    function renderDropdowns(currentMap) {
        $('#the-list tr[id^="post-"]').each(function(){
            var $row = $(this);
            var rowId = $row.attr('id') || '';
            var postId = parseInt(rowId.replace('post-', ''), 10);
            if (!postId) {
                return;
            }

            var $cell = $row.find('td.' + APT.columnClass);
            if (!$cell.length) {
                return;
            }

            var current = currentMap && currentMap[String(postId)] ? currentMap[String(postId)] : [];
            var $select = buildSelect(APT.terms, current, true, APT.placeholder);
            updateSelectEmptyState($select);

            $select.on('change', function(){
                var termIds = $(this).val() || [];
                var $thisSelect = $(this);
                updateSelectEmptyState($thisSelect);
                $thisSelect.prop('disabled', true);
                showInlineStatus($thisSelect, 'pending', 'Guardando...');

                $.post(APT.ajaxUrl, {
                    action: 'apt_set_term',
                    nonce: APT.saveTermNonce,
                    post_id: postId,
                    taxonomy: APT.taxonomy,
                    term_ids: termIds
                }).done(function(resp){
                    if (!resp || !resp.success) {
                        var msg = resp && resp.data && resp.data.message ? resp.data.message : 'No se pudo guardar el termino';
                        showInlineStatus($thisSelect, 'error', msg);
                        toast(msg);
                        return;
                    }
                    showInlineStatus($thisSelect, 'success', 'Guardado');
                    toast('Taxonomia actualizada');
                }).fail(function(){
                    showInlineStatus($thisSelect, 'error', 'Error de conexion');
                    toast('Error de conexion al guardar el termino');
                }).always(function(){
                    $thisSelect.prop('disabled', false);
                });
            });

            $cell.empty().append($select);
        });
    }

    function initInlineTaxonomyDropdown() {
        if (!window.APT || !APT.taxonomyEnabled || !APT.taxonomy || !APT.postType) {
            return;
        }

        var postIds = getPostIds();
        if (!postIds.length) {
            return;
        }

        $.post(APT.ajaxUrl, {
            action: 'apt_get_current_terms',
            nonce: APT.fetchNonce,
            post_type: APT.postType,
            taxonomy: APT.taxonomy,
            post_ids: postIds
        }).done(function(resp){
            if (resp && resp.success && resp.data && resp.data.current_terms) {
                renderDropdowns(resp.data.current_terms);
                return;
            }
            renderDropdowns({});
        }).fail(function(){
            renderDropdowns({});
        });
    }

    function renderSelectFieldDropdowns(currentMap) {
        $('#the-list tr[id^="post-"]').each(function(){
            var $row = $(this);
            var rowId = $row.attr('id') || '';
            var postId = parseInt(rowId.replace('post-', ''), 10);
            if (!postId) {
                return;
            }

            var $cell = $row.find('td.' + APT.selectFieldColumnClass);
            if (!$cell.length) {
                return;
            }

            var current = currentMap && currentMap[String(postId)] ? currentMap[String(postId)] : [];
            var $select = buildSelect(APT.selectFieldChoices, current, !!APT.selectFieldMultiple, APT.selectFieldPlaceholder || 'Seleccionar');
            updateSelectEmptyState($select);

            $select.on('change', function(){
                var selectedValues = $(this).val() || [];
                if (!Array.isArray(selectedValues)) {
                    selectedValues = selectedValues ? [selectedValues] : [];
                }

                var $thisSelect = $(this);
                updateSelectEmptyState($thisSelect);
                $thisSelect.prop('disabled', true);
                showInlineStatus($thisSelect, 'pending', 'Guardando...');

                $.post(APT.ajaxUrl, {
                    action: 'apt_set_select_field',
                    nonce: APT.saveSelectFieldNonce,
                    post_id: postId,
                    field_id: APT.selectFieldId,
                    values: selectedValues
                }).done(function(resp){
                    if (!resp || !resp.success) {
                        var msg = resp && resp.data && resp.data.message ? resp.data.message : 'No se pudo guardar el campo';
                        showInlineStatus($thisSelect, 'error', msg);
                        toast(msg);
                        return;
                    }
                    showInlineStatus($thisSelect, 'success', 'Guardado');
                    toast('Campo actualizado');
                }).fail(function(){
                    showInlineStatus($thisSelect, 'error', 'Error de conexion');
                    toast('Error de conexion al guardar el campo');
                }).always(function(){
                    $thisSelect.prop('disabled', false);
                });
            });

            $cell.empty().append($select);
        });
    }

    function initSelectFieldInline() {
        if (!window.APT || !APT.selectFieldEnabled || !APT.selectFieldId || !APT.postType) {
            return;
        }

        var postIds = getPostIds();
        if (!postIds.length) {
            return;
        }

        $.post(APT.ajaxUrl, {
            action: 'apt_get_current_select_field',
            nonce: APT.fetchSelectFieldNonce,
            post_type: APT.postType,
            field_id: APT.selectFieldId,
            post_ids: postIds
        }).done(function(resp){
            if (resp && resp.success && resp.data && resp.data.current_values) {
                renderSelectFieldDropdowns(resp.data.current_values);
                return;
            }
            renderSelectFieldDropdowns({});
        }).fail(function(){
            renderSelectFieldDropdowns({});
        });
    }

    function initFeaturedToggle() {
        if (!window.APT || !APT.featuredEnabled) {
            return;
        }

        $(document).on('change', '.apt-featured-toggle', function(){
            var $toggle = $(this);
            var postId = parseInt($toggle.data('post-id'), 10);
            var featured = $toggle.is(':checked') ? 1 : 0;

            if (!postId) {
                return;
            }

            $toggle.prop('disabled', true);
            showInlineStatus($toggle, 'pending', 'Guardando...');
            $.post(APT.ajaxUrl, {
                action: 'apt_set_featured',
                nonce: APT.saveFeaturedNonce,
                post_id: postId,
                featured: featured
            }).done(function(resp){
                if (!resp || !resp.success) {
                    var msg = resp && resp.data && resp.data.message ? resp.data.message : 'No se pudo actualizar destacado';
                    showInlineStatus($toggle, 'error', msg);
                    toast(msg);
                    $toggle.prop('checked', !featured);
                    return;
                }
                showInlineStatus($toggle, 'success', 'Guardado');
                toast('Producto destacado actualizado');
            }).fail(function(){
                showInlineStatus($toggle, 'error', 'Error de conexion');
                toast('Error de conexion al actualizar destacado');
                $toggle.prop('checked', !featured);
            }).always(function(){
                $toggle.prop('disabled', false);
            });
        });
    }

    function closeExcerptEditor() {
        $('#apt-excerpt-editor').remove();
    }

    function openExcerptEditor($button) {
        var $wrap = $button.closest('.apt-excerpt-inline-wrap');
        var postId = parseInt($wrap.data('post-id'), 10);
        var current = $button.data('full') || '';

        if (!postId) {
            return;
        }

        closeExcerptEditor();

        var offset = $button.offset();
        var $editor = $(
            '<div id="apt-excerpt-editor" class="apt-excerpt-editor">' +
                '<textarea class="apt-excerpt-textarea"></textarea>' +
                '<div class="apt-excerpt-actions">' +
                    '<button type="button" class="button button-primary apt-excerpt-save">OK</button>' +
                    '<button type="button" class="button apt-excerpt-cancel">Cancelar</button>' +
                '</div>' +
            '</div>'
        );

        $editor.css({
            position: 'absolute',
            top: (offset.top + $button.outerHeight() + 6) + 'px',
            left: offset.left + 'px',
            zIndex: 100000,
            width: '420px',
            background: '#fff',
            border: '1px solid #ccd0d4',
            borderRadius: '4px',
            padding: '10px',
            boxShadow: '0 8px 20px rgba(0,0,0,0.15)'
        });

        $editor.find('.apt-excerpt-textarea').val(current).css({ width: '100%', minHeight: '110px' });

        $editor.on('click', '.apt-excerpt-cancel', function(){
            closeExcerptEditor();
        });

        $editor.on('click', '.apt-excerpt-save', function(){
            var $save = $(this);
            var newExcerpt = $editor.find('.apt-excerpt-textarea').val();
            $save.prop('disabled', true);
            showInlineStatus($wrap, 'pending', 'Guardando...');

            $.post(APT.ajaxUrl, {
                action: 'apt_set_excerpt',
                nonce: APT.saveExcerptNonce,
                post_id: postId,
                excerpt: newExcerpt
            }).done(function(resp){
                if (!resp || !resp.success) {
                    var msg = resp && resp.data && resp.data.message ? resp.data.message : 'No se pudo guardar la descripcion corta';
                    showInlineStatus($wrap, 'error', msg);
                    toast(msg);
                    return;
                }

                var full = resp.data && typeof resp.data.excerpt !== 'undefined' ? resp.data.excerpt : newExcerpt;
                var preview = resp.data && typeof resp.data.preview !== 'undefined' ? resp.data.preview : full;
                $button.data('full', full);
                $wrap.find('.apt-excerpt-preview').val(preview);
                closeExcerptEditor();
                showInlineStatus($wrap, 'success', 'Guardado');
                toast('Descripcion corta actualizada');
            }).fail(function(){
                showInlineStatus($wrap, 'error', 'Error de conexion');
                toast('Error de conexion al guardar descripcion corta');
            }).always(function(){
                $save.prop('disabled', false);
            });
        });

        $('body').append($editor);
    }

    function initExcerptInline() {
        if (!window.APT || !APT.excerptEnabled) {
            return;
        }

        $(document).on('click', '.apt-excerpt-edit-btn', function(e){
            e.preventDefault();
            openExcerptEditor($(this));
        });

        $(document).on('click', '.apt-excerpt-preview', function(e){
            e.preventDefault();
            var $btn = $(this).closest('.apt-excerpt-inline-wrap').find('.apt-excerpt-edit-btn');
            if ($btn.length) {
                openExcerptEditor($btn);
            }
        });

        $(document).on('click', function(e){
            var $target = $(e.target);
            if (!$target.closest('#apt-excerpt-editor').length && !$target.closest('.apt-excerpt-edit-btn').length) {
                closeExcerptEditor();
            }
        });
    }

    $(document).ready(function(){
        initInlineTaxonomyDropdown();
        initSelectFieldInline();
        initFeaturedToggle();
        initExcerptInline();
    });
})(jQuery);
JS;
            wp_add_inline_script( $handle, $script );

            $style = <<<'CSS'
.apt-featured-switch {
    position: relative;
    display: inline-block;
    width: 42px;
    height: 22px;
}

.apt-featured-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.apt-featured-slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: #ccd0d4;
    transition: .2s;
    border-radius: 999px;
}

.apt-featured-slider:before {
    position: absolute;
    content: '';
    height: 16px;
    width: 16px;
    left: 3px;
    top: 3px;
    background: #fff;
    transition: .2s;
    border-radius: 50%;
}

.apt-featured-toggle:checked + .apt-featured-slider {
    background: #f0b849;
}

.apt-featured-toggle:checked + .apt-featured-slider:before {
    transform: translateX(20px);
}

.apt-excerpt-inline-wrap {
    display: flex;
    flex-wrap:wrap;
    gap: 6px;
    align-items: center;
    justify-content: flex-start;
}

.apt-excerpt-preview {
    width: 180px;
    max-width: 100%;
    font-size: 11px;
    cursor: pointer;
}

.apt-inline-status {
    display: none;
    margin-left: 8px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 10px;
    line-height: 1.6;
    vertical-align: middle;
}

.apt-inline-status.is-pending {
    background: #fef3c7;
    color: #7c4a03;
}

.apt-inline-status.is-success {
    background: #dcfce7;
    color: #14532d;
}

.apt-inline-status.is-error {
    background: #fee2e2;
    color: #7f1d1d;
}

.apt-inline-term-select.is-empty {
    box-shadow: 0 0 0 2px #dc2626;
    border-color: #dc2626;
}
CSS;
            $style_handle = 'apt-admin-list-tools-style';
            wp_register_style( $style_handle, false, array(), '1.1.0' );
            wp_enqueue_style( $style_handle );
            wp_add_inline_style( $style_handle, $style );
        }

        public function ajax_get_current_terms() {
            check_ajax_referer( self::NONCE_ACTION_FETCH_TERM, 'nonce' );

            if ( ! current_user_can( 'edit_posts' ) ) {
                wp_send_json_error( array( 'message' => 'Permisos insuficientes' ), 403 );
            }

            $post_type = isset( $_POST['post_type'] ) ? sanitize_key( wp_unslash( $_POST['post_type'] ) ) : '';
            $taxonomy = isset( $_POST['taxonomy'] ) ? sanitize_key( wp_unslash( $_POST['taxonomy'] ) ) : '';
            $post_ids = isset( $_POST['post_ids'] ) ? (array) $_POST['post_ids'] : array();

            if ( ! $post_type || ! $taxonomy ) {
                wp_send_json_error( array( 'message' => 'Parametros invalidos' ), 400 );
            }

            $mapping = $this->get_mapping();
            if ( empty( $mapping[ $post_type ] ) || $mapping[ $post_type ] !== $taxonomy ) {
                wp_send_json_error( array( 'message' => 'Taxonomia no habilitada para este tipo de post' ), 400 );
            }

            $result = array();
            foreach ( $post_ids as $raw_post_id ) {
                $post_id = absint( $raw_post_id );
                if ( ! $post_id ) {
                    continue;
                }

                $terms = wp_get_object_terms(
                    $post_id,
                    $taxonomy,
                    array(
                        'fields' => 'ids',
                    )
                );

                if ( is_wp_error( $terms ) || empty( $terms ) ) {
                    $result[ (string) $post_id ] = array();
                } else {
                    $result[ (string) $post_id ] = array_map( 'absint', $terms );
                }
            }

            wp_send_json_success( array( 'current_terms' => $result ) );
        }

        public function ajax_set_term() {
            check_ajax_referer( self::NONCE_ACTION_SAVE_TERM, 'nonce' );

            $post_id = isset( $_POST['post_id'] ) ? absint( $_POST['post_id'] ) : 0;
            $taxonomy = isset( $_POST['taxonomy'] ) ? sanitize_key( wp_unslash( $_POST['taxonomy'] ) ) : '';
            $raw_term_ids = isset( $_POST['term_ids'] ) ? (array) $_POST['term_ids'] : array();
            $term_ids = array();

            foreach ( $raw_term_ids as $raw_term_id ) {
                $term_id = absint( $raw_term_id );
                if ( $term_id > 0 ) {
                    $term_ids[] = $term_id;
                }
            }

            $term_ids = array_values( array_unique( $term_ids ) );

            if ( ! $post_id || ! $taxonomy ) {
                wp_send_json_error( array( 'message' => 'Parametros invalidos' ), 400 );
            }

            if ( ! current_user_can( 'edit_post', $post_id ) ) {
                wp_send_json_error( array( 'message' => 'No tienes permisos para editar este post' ), 403 );
            }

            $post_type = get_post_type( $post_id );
            if ( ! $post_type ) {
                wp_send_json_error( array( 'message' => 'Post no encontrado' ), 404 );
            }

            $mapping = $this->get_mapping();
            if ( empty( $mapping[ $post_type ] ) || $mapping[ $post_type ] !== $taxonomy ) {
                wp_send_json_error( array( 'message' => 'Taxonomia no habilitada para este tipo de post' ), 400 );
            }

            foreach ( $term_ids as $term_id ) {
                $term = get_term( $term_id, $taxonomy );
                if ( ! $term || is_wp_error( $term ) ) {
                    wp_send_json_error( array( 'message' => 'Termino invalido para esta taxonomia' ), 400 );
                }
            }

            $set_result = wp_set_object_terms( $post_id, $term_ids, $taxonomy, false );

            if ( is_wp_error( $set_result ) ) {
                wp_send_json_error( array( 'message' => $set_result->get_error_message() ), 500 );
            }

            wp_send_json_success( array( 'message' => 'Termino actualizado correctamente' ) );
        }

        public function ajax_get_current_select_field() {
            check_ajax_referer( self::NONCE_ACTION_FETCH_SELECT_FIELD, 'nonce' );

            if ( ! current_user_can( 'edit_posts' ) ) {
                wp_send_json_error( array( 'message' => 'Permisos insuficientes' ), 403 );
            }

            $post_type = isset( $_POST['post_type'] ) ? sanitize_key( wp_unslash( $_POST['post_type'] ) ) : '';
            $field_id = isset( $_POST['field_id'] ) ? sanitize_text_field( wp_unslash( $_POST['field_id'] ) ) : '';
            $post_ids = isset( $_POST['post_ids'] ) ? (array) $_POST['post_ids'] : array();

            if ( ! $post_type || ! $field_id ) {
                wp_send_json_error( array( 'message' => 'Parametros invalidos' ), 400 );
            }

            $field_config = $this->get_active_select_field_config_for_post_type( $post_type );
            if ( ! $field_config || $field_config['id'] !== $field_id ) {
                wp_send_json_error( array( 'message' => 'Campo no habilitado para este tipo de post' ), 400 );
            }

            $result = array();
            foreach ( $post_ids as $raw_post_id ) {
                $post_id = absint( $raw_post_id );
                if ( ! $post_id ) {
                    continue;
                }

                $result[ (string) $post_id ] = $this->get_select_field_values_for_post( $post_id, $field_config );
            }

            wp_send_json_success( array( 'current_values' => $result ) );
        }

        public function ajax_set_select_field() {
            check_ajax_referer( self::NONCE_ACTION_SAVE_SELECT_FIELD, 'nonce' );

            $post_id = isset( $_POST['post_id'] ) ? absint( $_POST['post_id'] ) : 0;
            $field_id = isset( $_POST['field_id'] ) ? sanitize_text_field( wp_unslash( $_POST['field_id'] ) ) : '';
            $raw_values = isset( $_POST['values'] ) ? (array) $_POST['values'] : array();

            if ( ! $post_id || ! $field_id ) {
                wp_send_json_error( array( 'message' => 'Parametros invalidos' ), 400 );
            }

            if ( ! current_user_can( 'edit_post', $post_id ) ) {
                wp_send_json_error( array( 'message' => 'No tienes permisos para editar este post' ), 403 );
            }

            $post_type = get_post_type( $post_id );
            if ( ! $post_type ) {
                wp_send_json_error( array( 'message' => 'Post no encontrado' ), 404 );
            }

            $field_config = $this->get_active_select_field_config_for_post_type( $post_type );
            if ( ! $field_config || $field_config['id'] !== $field_id ) {
                wp_send_json_error( array( 'message' => 'Campo no habilitado para este tipo de post' ), 400 );
            }

            $allowed_values = array();
            foreach ( $field_config['choices'] as $choice ) {
                $allowed_values[] = (string) $choice['value'];
            }

            $values = array();
            foreach ( $raw_values as $raw_value ) {
                $value = sanitize_text_field( wp_unslash( $raw_value ) );
                if ( '' === $value ) {
                    continue;
                }
                if ( in_array( $value, $allowed_values, true ) ) {
                    $values[] = $value;
                }
            }

            $values = array_values( array_unique( $values ) );

            if ( empty( $field_config['multiple'] ) && ! empty( $values ) ) {
                $values = array( $values[0] );
            }

            $this->save_select_field_values_for_post( $post_id, $field_config, $values );

            wp_send_json_success( array( 'values' => $values ) );
        }

        public function ajax_set_featured() {
            check_ajax_referer( self::NONCE_ACTION_SAVE_FEATURED, 'nonce' );

            $post_id = isset( $_POST['post_id'] ) ? absint( $_POST['post_id'] ) : 0;
            $featured = isset( $_POST['featured'] ) ? (int) $_POST['featured'] : 0;

            if ( ! $post_id ) {
                wp_send_json_error( array( 'message' => 'Post invalido' ), 400 );
            }

            if ( 'product' !== get_post_type( $post_id ) ) {
                wp_send_json_error( array( 'message' => 'Solo disponible para productos' ), 400 );
            }

            if ( ! current_user_can( 'edit_post', $post_id ) ) {
                wp_send_json_error( array( 'message' => 'Permisos insuficientes' ), 403 );
            }

            $is_featured = ( $featured > 0 );

            if ( function_exists( 'wc_get_product' ) ) {
                $product = wc_get_product( $post_id );
                if ( $product ) {
                    $product->set_featured( $is_featured );
                    $product->save();
                } else {
                    update_post_meta( $post_id, '_featured', $is_featured ? 'yes' : 'no' );
                }
            } else {
                update_post_meta( $post_id, '_featured', $is_featured ? 'yes' : 'no' );
            }

            wp_send_json_success( array( 'featured' => $is_featured ? 1 : 0 ) );
        }

        public function ajax_set_excerpt() {
            check_ajax_referer( self::NONCE_ACTION_SAVE_EXCERPT, 'nonce' );

            $post_id = isset( $_POST['post_id'] ) ? absint( $_POST['post_id'] ) : 0;
            $excerpt = isset( $_POST['excerpt'] ) ? sanitize_textarea_field( wp_unslash( $_POST['excerpt'] ) ) : '';

            if ( ! $post_id ) {
                wp_send_json_error( array( 'message' => 'Post invalido' ), 400 );
            }

            if ( ! current_user_can( 'edit_post', $post_id ) ) {
                wp_send_json_error( array( 'message' => 'Permisos insuficientes' ), 403 );
            }

            $updated = wp_update_post(
                array(
                    'ID' => $post_id,
                    'post_excerpt' => $excerpt,
                ),
                true
            );

            if ( is_wp_error( $updated ) ) {
                wp_send_json_error( array( 'message' => $updated->get_error_message() ), 500 );
            }

            $preview = $excerpt ? wp_trim_words( $excerpt, 14, '...' ) : '';
            wp_send_json_success(
                array(
                    'excerpt' => $excerpt,
                    'preview' => $preview,
                )
            );
        }

        private function get_mapping() {
            $mapping = get_option( self::OPTION_TAX_MAP, array() );
            return is_array( $mapping ) ? $mapping : array();
        }

        private function get_excerpt_map() {
            $map = get_option( self::OPTION_EXCERPT_MAP, array() );
            return is_array( $map ) ? $map : array();
        }

        private function get_select_field_map() {
            $map = get_option( self::OPTION_SELECT_FIELD_MAP, array() );
            return is_array( $map ) ? $map : array();
        }

        private function get_active_select_field_config_for_post_type( $post_type ) {
            $map = $this->get_select_field_map();
            if ( empty( $map[ $post_type ] ) ) {
                return null;
            }

            $field_id = $map[ $post_type ];
            $candidates = $this->get_select_field_candidates_for_post_type( $post_type );
            if ( empty( $candidates[ $field_id ] ) ) {
                return null;
            }

            return $candidates[ $field_id ];
        }

        private function is_excerpt_enabled_for_post_type( $post_type ) {
            $map = $this->get_excerpt_map();
            return ! empty( $map[ $post_type ] );
        }

        private function is_featured_async_enabled() {
            return (int) get_option( self::OPTION_FEATURED_ENABLED, 0 ) === 1;
        }
    }
}

new Admin_Power_Tools();
