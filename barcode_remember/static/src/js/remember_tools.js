odoo.define('barcode_remember.remember_tools', function (require) {
    'use strict'

    const {bus} = require('web.core')

    const {Component} = owl
    const {onMounted, onWillUnmount} = owl.hooks

    return {
        /**
         * @param {String} code
         * @param {()=>{}} [validate]
         * @param {()=>{}} [discard]
         * @param {()=>{}} [cancel]
         * @returns {boolean}
         * @public
         */
        catchCommandBarcode(code, {validate, discard, cancel}) {
            switch (code) {
                case 'O-BTN.validate':
                    if (typeof validate === 'function') {
                        validate()
                    }
                    return true
                case 'O-CMD.DISCARD':
                    if (typeof discard === 'function') {
                        discard()
                    }
                    return true
                case 'O-BTN.cancel':
                    if (typeof cancel === 'function') {
                        cancel()
                    }
                    return true

            }
            return false
        },
        /**
         * @param {(barcode:String)=>{}} callback
         */
        useBarcodeScanner(callback) {
            const component = Component.current
            onMounted(() => {
                component.trigger('listen_to_barcode_scanned', {'listen': false});
                bus.on('barcode_scanned', component, callback);
            })
            onWillUnmount(() => {
                component.trigger('listen_to_barcode_scanned', {'listen': true});
                bus.off('barcode_scanned', component, callback);
            })
        },
    }
});