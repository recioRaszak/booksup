<?php
/**
 * Plugin Name: Book Uploader REST Endpoints
 * Description: Añade endpoints para trabajar con el uploader de libros y gestionar marcas como taxonomy product_brand.
 * Version: 1.0.2
 * Author: Book Uploader
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'init', 'bu_register_product_brand_taxonomy' );
function bu_register_product_brand_taxonomy() {
    register_taxonomy( 'product_brand', array( 'product' ), array(
        'hierarchical' => false,
        'labels' => array(
            'name' => 'Product Brands',
            'singular_name' => 'Product Brand',
            'search_items' => 'Buscar marcas',
            'all_items' => 'Todas las marcas',
            'edit_item' => 'Editar marca',
            'update_item' => 'Actualizar marca',
            'add_new_item' => 'Añadir nueva marca',
            'new_item_name' => 'Nombre nueva marca',
            'menu_name' => 'Marcas'
        ),
        'show_ui' => true,
        'show_in_rest' => true,
        'rest_base' => 'product_brand',
        'rewrite' => array( 'slug' => 'product-brand' ),
        'public' => true,
    ) );
}

add_action( 'rest_api_init', 'bu_register_rest_routes' );
function bu_register_rest_routes() {
    // Debug endpoint para verificar que el plugin está cargado
    register_rest_route( 'book-uploader/v1', '/debug', array(
        array(
            'methods' => 'GET',
            'callback' => 'bu_debug_endpoint',
            'permission_callback' => '__return_true',
        ),
    ) );

    register_rest_route( 'book-uploader/v1', '/brands', array(
        array(
            'methods' => 'GET',
            'callback' => 'bu_get_brands',
            'permission_callback' => 'bu_rest_permissions_check',
        ),
        array(
            'methods' => 'POST',
            'callback' => 'bu_create_brand',
            'permission_callback' => 'bu_rest_permissions_check',
            'args' => array(
                'name' => array(
                    'required' => true,
                    'sanitize_callback' => 'sanitize_text_field',
                ),
            ),
        ),
    ) );

    register_rest_route( 'book-uploader/v1', '/products/(?P<id>\d+)/brand', array(
        array(
            'methods' => 'POST',
            'callback' => 'bu_assign_brand_to_product',
            'permission_callback' => 'bu_rest_permissions_check',
            'args' => array(
                'brand_id' => array(
                    'required' => true,
                    'sanitize_callback' => 'absint',
                ),
            ),
        ),
    ) );

    register_rest_route( 'book-uploader/v1', '/product-meta-fields', array(
        array(
            'methods' => 'GET',
            'callback' => 'bu_get_product_meta_fields',
            'permission_callback' => 'bu_rest_permissions_check',
        ),
    ) );
}

if ( ! function_exists( 'bu_rest_permissions_check' ) ) {
    function bu_rest_permissions_check() {
        if ( ! is_user_logged_in() ) {
            return new WP_Error(
                'bu_auth_required',
                'Debes iniciar sesion para usar este endpoint.',
                array( 'status' => 401 )
            );
        }

        if ( ! current_user_can( 'edit_posts' ) ) {
            return new WP_Error(
                'bu_insufficient_permissions',
                'No tienes permisos suficientes para usar este endpoint.',
                array( 'status' => 403 )
            );
        }

        return true;
    }
}

function bu_get_brands( $request ) {
    $search = $request->get_param( 'search' );
    $args = array(
        'taxonomy' => 'product_brand',
        'hide_empty' => false,
        'orderby' => 'name',
        'order' => 'ASC',
    );
    if ( $search ) {
        $args['search'] = sanitize_text_field( $search );
    }
    $terms = get_terms( $args );
    if ( is_wp_error( $terms ) ) {
        return new WP_Error( 'bu_get_brands_error', 'No se pudieron cargar las marcas', array( 'status' => 500 ) );
    }

    $result = array();
    foreach ( $terms as $term ) {
        $result[] = array(
            'id' => $term->term_id,
            'name' => $term->name,
        );
    }
    return rest_ensure_response( $result );
}

function bu_create_brand( $request ) {
    $name = sanitize_text_field( $request->get_param( 'name' ) );
    $existing = term_exists( $name, 'product_brand' );
    if ( $existing && ! is_wp_error( $existing ) ) {
        $term_id = is_array( $existing ) ? $existing['term_id'] : $existing;
        return rest_ensure_response( array( 'id' => $term_id, 'name' => $name ) );
    }

    $term = wp_insert_term( $name, 'product_brand' );
    if ( is_wp_error( $term ) ) {
        return new WP_Error( 'bu_create_brand_error', 'No se pudo crear la marca', array( 'status' => 500 ) );
    }

    return rest_ensure_response( array( 'id' => $term['term_id'], 'name' => $name ) );
}

function bu_assign_brand_to_product( $request ) {
    $product_id = absint( $request['id'] );
    $brand_id = absint( $request->get_param( 'brand_id' ) );

    if ( ! $product_id || ! $brand_id ) {
        return new WP_Error( 'bu_assign_brand_invalid', 'Producto o marca inválidos', array( 'status' => 400 ) );
    }

    $product = wc_get_product( $product_id );
    if ( ! $product ) {
        return new WP_Error( 'bu_assign_brand_no_product', 'Producto no encontrado', array( 'status' => 404 ) );
    }

    $result = wp_set_object_terms( $product_id, array( $brand_id ), 'product_brand', false );
    if ( is_wp_error( $result ) ) {
        return new WP_Error( 'bu_assign_brand_error', 'No se pudo asignar la marca', array( 'status' => 500 ) );
    }

    return rest_ensure_response( array( 'success' => true, 'brand_id' => $brand_id ) );
}

function bu_debug_endpoint( $request ) {
    global $wp_rest_server;
    
    $user = wp_get_current_user();
    $current_route = $request->get_route();
    
    $debug_info = array(
        'plugin_version' => '1.0.2',
        'plugin_active' => true,
        'rest_api_initialized' => ! empty( $wp_rest_server ),
        'current_user' => array(
            'ID' => $user->ID,
            'login' => $user->user_login,
            'email' => $user->user_email,
            'roles' => $user->roles,
        ),
        'capabilities' => array(
            'edit_posts' => current_user_can( 'edit_posts' ),
            'manage_woocommerce' => current_user_can( 'manage_woocommerce' ),
            'manage_product_terms' => current_user_can( 'manage_product_terms' ),
        ),
        'current_request_route' => $current_route,
        'timestamp' => current_time( 'mysql' ),
    );
    
    return rest_ensure_response( $debug_info );
}

if ( ! function_exists( 'bu_normalize_acf_choices' ) ) {
    function bu_normalize_acf_choices( $raw_choices, $acf_type ) {
        $normalized = array();

        if ( is_array( $raw_choices ) ) {
            foreach ( $raw_choices as $choice_key => $choice_label ) {
                $choice_key = sanitize_text_field( (string) $choice_key );
                $choice_label = sanitize_text_field( (string) $choice_label );
                if ( $choice_key === '' && $choice_label === '' ) {
                    continue;
                }
                if ( $choice_key === '' ) {
                    $choice_key = $choice_label;
                }
                if ( $choice_label === '' ) {
                    $choice_label = $choice_key;
                }
                $normalized[ $choice_key ] = $choice_label;
            }
        } elseif ( is_string( $raw_choices ) && $raw_choices !== '' ) {
            $lines = preg_split( '/\r\n|\r|\n/', $raw_choices );
            if ( is_array( $lines ) ) {
                foreach ( $lines as $line ) {
                    $line = trim( $line );
                    if ( $line === '' ) {
                        continue;
                    }

                    if ( strpos( $line, ':' ) !== false ) {
                        $parts = explode( ':', $line, 2 );
                        $choice_key = sanitize_text_field( trim( $parts[0] ) );
                        $choice_label = sanitize_text_field( trim( $parts[1] ) );
                    } else {
                        $choice_key = sanitize_text_field( $line );
                        $choice_label = $choice_key;
                    }

                    if ( $choice_key === '' && $choice_label === '' ) {
                        continue;
                    }
                    if ( $choice_key === '' ) {
                        $choice_key = $choice_label;
                    }
                    if ( $choice_label === '' ) {
                        $choice_label = $choice_key;
                    }

                    $normalized[ $choice_key ] = $choice_label;
                }
            }
        }

        if ( empty( $normalized ) && in_array( $acf_type, array( 'true_false', 'boolean' ), true ) ) {
            $normalized = array(
                '1' => 'Si',
                '0' => 'No',
            );
        }

        return $normalized;
    }
}

if ( ! function_exists( 'bu_extract_acf_choices' ) ) {
    function bu_extract_acf_choices( $acf_field, $acf_type ) {
        if ( ! is_array( $acf_field ) ) {
            return bu_normalize_acf_choices( array(), $acf_type );
        }

        if ( isset( $acf_field['choices'] ) ) {
            return bu_normalize_acf_choices( $acf_field['choices'], $acf_type );
        }

        return bu_normalize_acf_choices( array(), $acf_type );
    }
}

function bu_get_product_meta_fields( $request ) {
    $fields = array();
    $known_keys = array();

    // Debug: Log access
    error_log( '[Book Uploader] bu_get_product_meta_fields called at ' . current_time( 'mysql' ) );

    // 1) Campos ACF aplicados a products, si ACF está activo.
    if ( function_exists( 'acf_get_field_groups' ) && function_exists( 'acf_get_fields' ) ) {
        $groups = acf_get_field_groups();
        if ( is_array( $groups ) ) {
            foreach ( $groups as $group ) {
                $acf_fields = acf_get_fields( $group );
                if ( ! is_array( $acf_fields ) ) {
                    continue;
                }

                $group_name = ! empty( $group['title'] ) ? sanitize_text_field( (string) $group['title'] ) : 'ACF';
                $group_key = ! empty( $group['key'] ) ? sanitize_text_field( (string) $group['key'] ) : '';

                foreach ( $acf_fields as $acf_field ) {
                    if ( empty( $acf_field['name'] ) ) {
                        continue;
                    }

                    $key = sanitize_text_field( $acf_field['name'] );
                    if ( ! $key || isset( $known_keys[ $key ] ) ) {
                        continue;
                    }

                    $acf_field_key = isset( $acf_field['key'] ) ? (string) $acf_field['key'] : '';
                    $canonical_field = $acf_field;

                    if ( $acf_field_key && function_exists( 'acf_get_field' ) ) {
                        $full_field = acf_get_field( $acf_field_key );
                        if ( is_array( $full_field ) ) {
                            $canonical_field = $full_field;
                        }
                    }

                    $acf_type = isset( $canonical_field['type'] ) ? $canonical_field['type'] : ( isset( $acf_field['type'] ) ? $acf_field['type'] : 'text' );
                    $choices = bu_extract_acf_choices( $canonical_field, $acf_type );

                    $known_keys[ $key ] = true;
                    $fields[] = array(
                        'key' => $key,
                        'label' => isset( $canonical_field['label'] ) ? $canonical_field['label'] : ( isset( $acf_field['label'] ) ? $acf_field['label'] : $key ),
                        'source' => 'acf',
                        'type' => $acf_type,
                        'choices' => $choices,
                        'acf_field_key' => $acf_field_key,
                        'group_name' => $group_name,
                        'group_key' => $group_key,
                    );
                }
            }
        }
    }

    // 2) Custom fields existentes en productos recientes (post meta visibles).
    $product_ids = get_posts( array(
        'post_type' => 'product',
        'post_status' => array( 'publish', 'draft', 'private' ),
        'posts_per_page' => 50,
        'fields' => 'ids',
        'orderby' => 'date',
        'order' => 'DESC',
    ) );

    if ( is_array( $product_ids ) ) {
        foreach ( $product_ids as $product_id ) {
            $meta = get_post_meta( $product_id );
            if ( ! is_array( $meta ) ) {
                continue;
            }

            foreach ( $meta as $meta_key => $meta_values ) {
                // Excluir metadatos privados/técnicos de WP/WC.
                if ( ! is_string( $meta_key ) || strpos( $meta_key, '_' ) === 0 ) {
                    continue;
                }
                if ( isset( $known_keys[ $meta_key ] ) ) {
                    continue;
                }

                $known_keys[ $meta_key ] = true;
                $fields[] = array(
                    'key' => $meta_key,
                    'label' => $meta_key,
                    'source' => 'meta',
                    'type' => 'text',
                    'choices' => array(),
                    'acf_field_key' => '',
                    'group_name' => 'Metacampos detectados',
                    'group_key' => 'meta-detected',
                );
            }
        }
    }

    usort( $fields, function( $a, $b ) {
        $group_cmp = strcasecmp( isset( $a['group_name'] ) ? $a['group_name'] : '', isset( $b['group_name'] ) ? $b['group_name'] : '' );
        if ( 0 !== $group_cmp ) {
            return $group_cmp;
        }
        return strcasecmp( $a['label'], $b['label'] );
    } );

    return rest_ensure_response( array( 'fields' => $fields ) );
}
