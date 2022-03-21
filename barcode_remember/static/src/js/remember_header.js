odoo.define('barcode_remember.remember_header', function (require) {
    'use strict'

    const HeaderWidget = require('stock_barcode.HeaderWidget');

    HeaderWidget.include({
        init: function (parent) {
            this._super.apply(this, arguments);
            this.mode = parent.mode
            this.includeWarranty = false
            this.includeGift = false
        },

        /**
         * @param {Boolean} [includeWarranty]
         * @param {Boolean} [includeGift]
         * @public
         */
        updateRememberState({includeWarranty, includeGift}) {
            if (includeWarranty !== undefined) {
                this.includeWarranty = includeWarranty
            }
            if (includeGift !== undefined) {
                this.includeGift = includeGift
            }
        },
    })

});