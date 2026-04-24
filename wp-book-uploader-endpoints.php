<?php
/**
 * Plugin Name: Book Uploader REST Endpoints
 * Description: Añade endpoints para trabajar con el uploader de libros y gestionar marcas como taxonomy product_brand.
 * Version: 1.0.0
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
}

function bu_rest_permissions_check() {
    return current_user_can( 'edit_posts' );
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
