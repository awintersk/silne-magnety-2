odoo.define('barcode_remember.remember_header', function (require) {
    'use strict'

    const HeaderWidget = require('stock_barcode.HeaderWidget');

    HeaderWidget.include({
        init: function (parent) {
            this._super.apply(this, arguments);
            this.mode = parent.mode
            this.includeLangWarning = false
            this.includeGift = false
        },

        /**
         * @param {Boolean} [includeLangWarning]
         * @param {Boolean} [includeGift]
         * @public
         */
        updateRememberState({includeLangWarning, includeGift}) {
            if (includeLangWarning !== undefined) {
                this.includeWarning = includeLangWarning
            }
            if (includeGift !== undefined) {
                this.includeGift = includeGift
            }
        },
    })

});